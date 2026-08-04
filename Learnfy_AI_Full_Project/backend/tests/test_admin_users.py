from datetime import datetime,timezone,timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config.database import Base,get_db
from app.models import academic,admin_audit,auth_token,chat,flashcard,group,note,notification,payment,quiz,resource,student_verification,subject,teacher_verification,user  # noqa:F401
from app.models.admin_audit import AdminAudit
from app.models.auth_token import AuthToken
from app.models.user import User,UserRole
from app.routes import admin
from app.services.auth_service import build_access_token

def test_admin_user_deactivation_restore_and_protections():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool);Base.metadata.create_all(engine);Session=sessionmaker(bind=engine);db=Session()
    actor=User(name="Admin",email="admin@test.dev",password="x",role=UserRole.admin,is_active=True)
    target=User(name="Student",email="student@test.dev",password="x",role=UserRole.student,is_active=True)
    db.add_all([actor,target]);db.commit();db.add(AuthToken(user_id=target.id,token_hash="x"*64,token_type="refresh",expires_at=datetime.now(timezone.utc)+timedelta(days=1)));db.commit()
    app=FastAPI();app.include_router(admin.router)
    def override_db(): yield db
    app.dependency_overrides[get_db]=override_db;client=TestClient(app);headers={"Authorization":f"Bearer {build_access_token(actor)}"}
    assert client.put(f"/admin/users/{actor.id}/deactivate",headers=headers,json={"reason":"self test"}).status_code==403
    assert client.request("DELETE",f"/admin/users/{actor.id}",headers=headers,json={"reason":"self deletion"}).status_code==403
    response=client.put(f"/admin/users/{target.id}/deactivate",headers=headers,json={"reason":"Policy violation"});assert response.status_code==200
    db.refresh(target);assert not target.is_active and target.deleted_at and db.query(AuthToken).filter_by(user_id=target.id,is_revoked=True).count()==1
    assert db.query(AdminAudit).filter_by(action="user.deactivate",target_id=target.id).count()==1
    active_users=client.get("/admin/users",headers=headers).json();assert [item["id"] for item in active_users]==[actor.id]
    page=client.get("/admin/users/page",headers=headers,params={"status":"all","page_size":5}).json();assert page["total"]==2 and len(page["items"])==2
    response=client.put(f"/admin/users/{target.id}/restore",headers=headers,json={"reason":"Appeal accepted"});assert response.status_code==200
    db.refresh(target);assert target.is_active and target.deleted_at is None
    assert client.put(f"/admin/users/{actor.id}/deactivate",headers=headers,json={"reason":"final admin"}).status_code==403
    db.close()
