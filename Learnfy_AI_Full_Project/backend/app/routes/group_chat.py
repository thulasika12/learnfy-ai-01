"""Secure real-time messaging layered onto the existing Study Group discussions."""
import os
import uuid
from io import BytesIO
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pypdf import PdfReader
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.config.database import SessionLocal, get_db
from app.config.security import decode_access_token
from app.config.settings import settings
from app.models.group import GroupDiscussion, GroupMember, GroupMessageReaction, GroupMessageRead, GroupMessageReport, StudyGroup
from app.models.note import Note
from app.models.resource import Resource
from app.models.user import User, UserRole
from app.services.audit_service import add_admin_audit
from app.services.group_safety import PHOTO_BLOCKED_MESSAGE, validate_group_text
from app.services.storage_service import delete_file, file_response, store_bytes
from app.utils.dependencies import get_current_user

router=APIRouter(prefix="/groups",tags=["Study Group Chat"])
connections: dict[int, dict[int, set[WebSocket]]] = defaultdict(lambda: defaultdict(set))
send_windows: dict[tuple[int,int],deque] = defaultdict(deque)

class MessageBody(BaseModel):
    message: str=Field(min_length=1,max_length=4000)
    reply_to_message_id: Optional[int]=None
class EditBody(BaseModel): message: str=Field(min_length=1,max_length=4000)
class ReactionBody(BaseModel): emoji: str=Field(min_length=1,max_length=16)
class ReportBody(BaseModel): reason: str=Field(min_length=3,max_length=500)
class ReadBody(BaseModel): message_id: int
class ShareBody(BaseModel): resource_type: str; resource_id: int; reply_to_message_id: Optional[int]=None
class MuteBody(BaseModel): minutes: int=Field(ge=0,le=10080)

def member(db,group_id,user_id):
    membership=db.query(GroupMember).filter_by(group_id=group_id,user_id=user_id).first()
    if not membership: raise HTTPException(403,"Approved group membership is required")
    return membership

def safe_user(user):
    role=getattr(user.role,"value",user.role); verification=getattr(user.student_verification_status,"value",user.student_verification_status)
    return {"id":user.id,"name":user.name,"profile_image":user.profile_image,"academic_role":role,"is_verified":bool(user.is_verified_teacher or verification=="verified")}

def resource_card(item,db):
    if item.learning_resource_type=="note": source=db.query(Note).filter_by(id=item.learning_resource_id,is_hidden=False).first()
    elif item.learning_resource_type=="resource": source=db.query(Resource).filter_by(id=item.learning_resource_id,is_hidden=False).first()
    else: source=None
    return {"type":item.learning_resource_type,"id":source.id,"title":source.title,"subject":source.subject,"grade":source.grade,"medium":source.medium,"action_url":f"/groups/{item.group_id}/messages/{item.id}/learning-resource"} if source else None

def serialize(item,db):
    reactions={}
    for reaction in item.reactions:
        entry=reactions.setdefault(reaction.emoji,{"emoji":reaction.emoji,"count":0,"user_ids":[]}); entry["count"]+=1; entry["user_ids"].append(reaction.user_id)
    card=resource_card(item,db)
    attachment_url=f"/groups/{item.group_id}/messages/{item.id}/attachment" if item.attachment_url and item.message_type=="pdf" and not item.deleted_at else card["action_url"] if card and not item.deleted_at else None
    attachment_name=item.attachment_name or (" · ".join(str(value) for value in [card["title"],card["resource_type"],card["subject"],card["grade"],card["medium"]] if value) if card else None)
    return {"id":item.id,"group_id":item.group_id,"user_id":item.user_id,"message":"This message was deleted." if item.deleted_at else item.message,"message_type":"pdf" if card else item.message_type,"attachment_url":attachment_url,"attachment_name":attachment_name,"attachment_size":item.attachment_size,"learning_resource":card,"reply_to_message_id":item.reply_to_message_id,"reply_to":{"id":item.reply_to.id,"message":item.reply_to.message[:180],"user_name":item.reply_to.user.name} if item.reply_to else None,"edited_at":item.edited_at.isoformat() if item.edited_at else None,"deleted_at":item.deleted_at.isoformat() if item.deleted_at else None,"created_at":item.created_at.isoformat(),"user":safe_user(item.user),"reactions":list(reactions.values())}

def query_message(db,message_id):
    return db.query(GroupDiscussion).options(joinedload(GroupDiscussion.user),joinedload(GroupDiscussion.reply_to).joinedload(GroupDiscussion.user),joinedload(GroupDiscussion.reactions)).filter(GroupDiscussion.id==message_id).first()

async def broadcast(group_id,event):
    stale=[]
    for sockets in list(connections[group_id].values()):
        for socket in list(sockets):
            try: await socket.send_json(event)
            except Exception: stale.append(socket)
    for socket in stale:
        for sockets in connections[group_id].values(): sockets.discard(socket)

@router.get("/{group_id}/messages")
def history(group_id:int,before_id:Optional[int]=None,limit:int=50,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); limit=max(1,min(limit,100))
    query=db.query(GroupDiscussion).options(joinedload(GroupDiscussion.user),joinedload(GroupDiscussion.reply_to).joinedload(GroupDiscussion.user),joinedload(GroupDiscussion.reactions)).filter(GroupDiscussion.group_id==group_id)
    if before_id: query=query.filter(GroupDiscussion.id<before_id)
    rows=list(reversed(query.order_by(GroupDiscussion.id.desc()).limit(limit+1).all()))
    has_more=len(rows)>limit
    if has_more: rows=rows[1:]
    return {"items":[serialize(row,db) for row in rows],"has_more":has_more,"next_cursor":rows[0].id if rows else None}

@router.post("/{group_id}/messages",status_code=201)
async def send(group_id:int,payload:MessageBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    membership=member(db,group_id,user.id)
    now=datetime.now(timezone.utc).timestamp(); window=send_windows[(group_id,user.id)]
    while window and now-window[0]>10: window.popleft()
    if len(window)>=12: raise HTTPException(429,"You are sending messages too quickly")
    window.append(now)
    if membership.muted_until and membership.muted_until>datetime.now(timezone.utc): raise HTTPException(403,"You are temporarily muted")
    if payload.reply_to_message_id and not db.query(GroupDiscussion).filter_by(id=payload.reply_to_message_id,group_id=group_id).first(): raise HTTPException(400,"Invalid reply target")
    item=GroupDiscussion(group_id=group_id,user_id=user.id,message=validate_group_text(payload.message),reply_to_message_id=payload.reply_to_message_id)
    db.add(item); db.commit(); item=query_message(db,item.id); data=serialize(item,db); await broadcast(group_id,{"type":"message.created","message":data}); return data

@router.patch("/{group_id}/messages/{message_id}")
async def edit(group_id:int,message_id:int,payload:EditBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); item=query_message(db,message_id)
    if not item or item.group_id!=group_id: raise HTTPException(404,"Message not found")
    if item.user_id!=user.id: raise HTTPException(403,"You can only edit your own messages")
    if item.deleted_at: raise HTTPException(409,"Deleted messages cannot be edited")
    item.message=validate_group_text(payload.message); item.edited_at=datetime.now(timezone.utc); db.commit(); item=query_message(db,item.id); data=serialize(item,db); await broadcast(group_id,{"type":"message.updated","message":data}); return data

@router.delete("/{group_id}/messages/{message_id}")
async def delete_message(group_id:int,message_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    membership=db.query(GroupMember).filter_by(group_id=group_id,user_id=user.id).first()
    if not membership and user.role!=UserRole.admin: raise HTTPException(403,"Approved group membership is required")
    item=query_message(db,message_id)
    if not item or item.group_id!=group_id: raise HTTPException(404,"Message not found")
    if item.user_id!=user.id and (not membership or membership.role!="admin") and user.role!=UserRole.admin: raise HTTPException(403,"Insufficient permission")
    attachment=item.attachment_url
    item.deleted_at=datetime.now(timezone.utc); item.message=""; item.attachment_url=None
    if item.user_id!=user.id: add_admin_audit(db,user.id,"group_message_removed","group_message",item.id,"Removed by group or platform admin")
    db.commit(); delete_file(attachment,local_root="app/private/group-chat"); item=query_message(db,item.id); data=serialize(item,db); await broadcast(group_id,{"type":"message.updated","message":data}); return data

@router.post("/{group_id}/messages/{message_id}/reactions")
async def react(group_id:int,message_id:int,payload:ReactionBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); item=query_message(db,message_id)
    if not item or item.group_id!=group_id: raise HTTPException(404,"Message not found")
    existing=db.query(GroupMessageReaction).filter_by(message_id=message_id,user_id=user.id,emoji=payload.emoji).first()
    if existing: db.delete(existing)
    else: db.add(GroupMessageReaction(message_id=message_id,user_id=user.id,emoji=payload.emoji))
    db.commit(); item=query_message(db,message_id); data=serialize(item,db); await broadcast(group_id,{"type":"message.updated","message":data}); return data

@router.post("/{group_id}/messages/{message_id}/report",status_code=201)
def report(group_id:int,message_id:int,payload:ReportBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id)
    if not db.query(GroupDiscussion).filter_by(id=message_id,group_id=group_id).first(): raise HTTPException(404,"Message not found")
    if db.query(GroupMessageReport).filter_by(message_id=message_id,reporter_id=user.id).first(): raise HTTPException(409,"Message already reported")
    db.add(GroupMessageReport(message_id=message_id,reporter_id=user.id,reason=payload.reason)); add_admin_audit(db,user.id,"group_message_reported","group_message",message_id,"Safety report submitted; reporter identity is restricted") ; db.commit(); return {"message":"Report submitted"}

@router.post("/{group_id}/attachments",status_code=201)
async def upload(group_id:int,file:UploadFile=File(...),reply_to_message_id:Optional[int]=Form(None),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id)
    if Path(file.filename or "").suffix.lower() != ".pdf" or (file.content_type or "").lower() != "application/pdf": raise HTTPException(415,PHOTO_BLOCKED_MESSAGE)
    data=file.file.read(settings.MAX_UPLOAD_SIZE_MB*1024*1024+1); file.file.close()
    if len(data)>settings.MAX_UPLOAD_SIZE_MB*1024*1024: raise HTTPException(413,f"File exceeds {settings.MAX_UPLOAD_SIZE_MB}MB limit")
    if not data.startswith(b"%PDF-"): raise HTTPException(400,"Invalid or corrupted PDF study material")
    try:
        reader=PdfReader(BytesIO(data)); _=len(reader.pages)
        if reader.is_encrypted: raise ValueError("encrypted")
    except Exception:
        raise HTTPException(400,"Invalid, corrupted or password-protected PDF study material")
    storage_name=store_bytes(data,"private/group-chat",".pdf","application/pdf",Path(file.filename).name,private=True,local_root="app/private/group-chat")
    item=GroupDiscussion(group_id=group_id,user_id=user.id,message=Path(file.filename).name,reply_to_message_id=reply_to_message_id,message_type="pdf",attachment_url=storage_name,attachment_name=Path(file.filename).name,attachment_size=len(data)); db.add(item); db.commit(); data=serialize(query_message(db,item.id),db); await broadcast(group_id,{"type":"message.created","message":data}); return data

@router.get("/{group_id}/shareable-resources")
def shareable_resources(group_id:int,search:str="",db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); pattern=f"%{search[:100]}%"
    notes=db.query(Note).filter(Note.is_hidden.is_(False),Note.title.ilike(pattern)).order_by(Note.created_at.desc()).limit(30).all()
    resources=db.query(Resource).filter(Resource.is_hidden.is_(False),Resource.title.ilike(pattern)).order_by(Resource.created_at.desc()).limit(30).all()
    safe=lambda item,kind:{"id":item.id,"resource_type":kind,"title":item.title,"subject":item.subject,"grade":item.grade,"medium":item.medium}
    return [safe(item,"note") for item in notes]+[safe(item,"resource") for item in resources]

@router.post("/{group_id}/learning-resources",status_code=201)
async def share_resource(group_id:int,payload:ShareBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id)
    source=db.query(Note).filter_by(id=payload.resource_id,is_hidden=False).first() if payload.resource_type=="note" else db.query(Resource).filter_by(id=payload.resource_id,is_hidden=False).first() if payload.resource_type=="resource" else None
    if not source: raise HTTPException(404,"Learning resource not found or unavailable")
    item=GroupDiscussion(group_id=group_id,user_id=user.id,message=source.title,message_type="learning_resource",learning_resource_type=payload.resource_type,learning_resource_id=source.id,reply_to_message_id=payload.reply_to_message_id)
    db.add(item); db.commit(); data=serialize(query_message(db,item.id),db); await broadcast(group_id,{"type":"message.created","message":data}); return data

def safe_download_path(relative_url:str):
    relative=relative_url.removeprefix("/uploads/"); root=Path(settings.UPLOAD_DIR).resolve(); path=(root/relative).resolve()
    if root not in path.parents or not path.is_file(): raise HTTPException(404,"File not found")
    return path

@router.get("/{group_id}/messages/{message_id}/attachment")
def download_attachment(group_id:int,message_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); item=db.query(GroupDiscussion).filter_by(id=message_id,group_id=group_id).first()
    if not item or item.deleted_at or item.message_type!="pdf" or not item.attachment_url: raise HTTPException(404,"Attachment not found")
    return file_response(item.attachment_url,media_type="application/pdf",filename=item.attachment_name,local_root="app/private/group-chat")

@router.get("/{group_id}/messages/{message_id}/learning-resource")
def download_resource(group_id:int,message_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); item=db.query(GroupDiscussion).filter_by(id=message_id,group_id=group_id).first()
    if not item or item.deleted_at: raise HTTPException(404,"Learning resource not found")
    source=db.query(Note).filter_by(id=item.learning_resource_id,is_hidden=False).first() if item.learning_resource_type=="note" else db.query(Resource).filter_by(id=item.learning_resource_id,is_hidden=False).first()
    if not source or not source.file_url: raise HTTPException(404,"Learning resource file not found")
    return file_response(source.file_url,filename=Path(source.file_url).name)

@router.get("/{group_id}/members")
def members(group_id:int,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); rows=db.query(GroupMember).options(joinedload(GroupMember.user)).filter_by(group_id=group_id).all()
    return [{**safe_user(row.user),"group_role":row.role,"muted_until":row.muted_until if row.role=="member" else None} for row in rows]

@router.post("/{group_id}/members/{member_id}/mute")
def mute_member(group_id:int,member_id:int,payload:MuteBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    actor=member(db,group_id,user.id)
    if actor.role!="admin" and user.role!=UserRole.admin: raise HTTPException(403,"Group admin permission required")
    target=db.query(GroupMember).filter_by(group_id=group_id,user_id=member_id).first()
    if not target or target.role=="admin": raise HTTPException(400,"Member cannot be muted")
    from datetime import timedelta
    target.muted_until=datetime.now(timezone.utc)+timedelta(minutes=payload.minutes) if payload.minutes else None
    add_admin_audit(db,user.id,"group_member_muted" if payload.minutes else "group_member_unmuted","group_member",target.id,f"Duration minutes: {payload.minutes}"); db.commit(); return {"ok":True}

@router.post("/{group_id}/read")
def mark_read(group_id:int,payload:ReadBody,db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    member(db,group_id,user.id); state=db.query(GroupMessageRead).filter_by(group_id=group_id,user_id=user.id).first()
    if not state: state=GroupMessageRead(group_id=group_id,user_id=user.id); db.add(state)
    if not db.query(GroupDiscussion).filter_by(id=payload.message_id,group_id=group_id).first(): raise HTTPException(400,"Invalid read marker")
    state.last_read_message_id=payload.message_id; db.commit(); return {"ok":True}

@router.get("/unread-counts/me")
def unread(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    memberships=db.query(GroupMember.group_id).filter_by(user_id=user.id).all(); result={}
    for (group_id,) in memberships:
        state=db.query(GroupMessageRead).filter_by(group_id=group_id,user_id=user.id).first(); last=state.last_read_message_id if state else 0
        result[group_id]=db.query(func.count(GroupDiscussion.id)).filter(GroupDiscussion.group_id==group_id,GroupDiscussion.id>last,GroupDiscussion.user_id!=user.id).scalar() or 0
    return result

@router.websocket("/{group_id}/ws")
async def websocket_chat(websocket:WebSocket,group_id:int):
    protocols=websocket.headers.get("sec-websocket-protocol","").split(","); protocols=[p.strip() for p in protocols]
    token=protocols[1] if len(protocols)>1 and protocols[0]=="learnfy" else None; payload=decode_access_token(token or "")
    if not payload: await websocket.close(code=4401); return
    db=SessionLocal()
    try:
        user=db.query(User).filter(User.id==int(payload.get("sub",0)),User.is_active.is_(True)).first()
        if not user or not db.query(GroupMember).filter_by(group_id=group_id,user_id=user.id).first(): await websocket.close(code=4403); return
        await websocket.accept(subprotocol="learnfy"); connections[group_id][user.id].add(websocket); await broadcast(group_id,{"type":"presence","online_user_ids":list(connections[group_id])})
        while True:
            event=await websocket.receive_json()
            if event.get("type")=="typing": await broadcast(group_id,{"type":"typing","user_id":user.id,"name":user.name,"active":bool(event.get("active"))})
            elif event.get("type")=="message":
                try: validate_group_text(str(event.get("message", "")))
                except HTTPException as error: await websocket.send_json({"type":"error","detail":error.detail})
            elif event.get("type")=="ping": await websocket.send_json({"type":"pong"})
    except WebSocketDisconnect: pass
    finally:
        if 'user' in locals() and user: connections[group_id][user.id].discard(websocket);
        if 'user' in locals() and user and not connections[group_id][user.id]: connections[group_id].pop(user.id,None)
        await broadcast(group_id,{"type":"presence","online_user_ids":list(connections[group_id])}); db.close()
