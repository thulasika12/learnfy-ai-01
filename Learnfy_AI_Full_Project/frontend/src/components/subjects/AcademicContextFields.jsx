import { useState } from "react";
import EducationLevelSelect from "./EducationLevelSelect";
import GradeSelect from "./GradeSelect";
import MediumSelect from "./MediumSelect";
import StreamSelect from "./StreamSelect";
import SubjectSelect from "./SubjectSelect";
import { usePreferences } from "../../hooks/usePreferences";

export const emptyAcademicContext = { educationLevelId:"", levelCode:"", gradeId:"", grade:"", medium:"", stream:"", streamId:null, subject:"", subjectId:null };

export default function AcademicContextFields({ value, onChange, requireSubject=true, className="grid gap-3 sm:grid-cols-2" }) {
  const { t }=usePreferences();
  const [subjectTouched,setSubjectTouched]=useState(false);
  const set=(patch)=>onChange({...value,...patch});
  const schoolLevel=["PRIMARY","JUNIOR","OL","AL"].includes(value.levelCode);
  const customLevel=["SELF","UNIVERSITY","TEACHER"].includes(value.levelCode);
  const subjectInvalid=requireSubject&&value.subject.trim().length<2;
  return <div className={className}>
    <EducationLevelSelect value={value.educationLevelId} onChange={(id,item)=>{setSubjectTouched(false);set({educationLevelId:id,levelCode:item?.code||"",gradeId:"",grade:"",stream:"",streamId:null,subject:"",subjectId:null})}} required />
    {schoolLevel&&<GradeSelect levelId={value.educationLevelId} value={value.gradeId} onChange={(id,item)=>set({gradeId:id,grade:item?.name_en||"",stream:"",streamId:null,subject:"",subjectId:null})} required />}
    <MediumSelect value={value.medium} onChange={(medium)=>set({medium,subject:"",subjectId:null})} required />
    {value.levelCode==="AL"&&<StreamSelect value={value.stream} onChange={(stream,item)=>set({stream,streamId:item?.id||null,subject:"",subjectId:null})} required />}
    <div className={value.levelCode==="AL"?"sm:col-span-2":""}>
      {customLevel?<>
        <input className="input-field" value={value.subject} placeholder={t("academic.enterSubject")} aria-invalid={subjectTouched&&subjectInvalid} required={requireSubject} minLength={requireSubject?2:undefined} onChange={(event)=>{setSubjectTouched(false);set({subject:event.target.value,subjectId:null})}} onBlur={(event)=>{const subject=event.target.value.trim();setSubjectTouched(true);set({subject,subjectId:null})}} onInvalid={(event)=>{event.preventDefault();setSubjectTouched(true)}}/>
        {subjectTouched&&subjectInvalid&&<p className="mt-1 text-xs text-red-500" role="alert">{t("academic.subjectRequired")}</p>}
      </>:<SubjectSelect gradeId={value.gradeId} medium={value.medium} level={!value.gradeId?value.levelCode:""} stream={value.levelCode==="AL"?value.stream:""} value={value.subject} selectedId={value.subjectId} onChange={(subject,item)=>set({subject,subjectId:item?.id||null})} required={requireSubject} disabled={!value.educationLevelId||(schoolLevel&&!value.gradeId)||(value.levelCode==="AL"&&!value.stream)} />}
    </div>
  </div>;
}
