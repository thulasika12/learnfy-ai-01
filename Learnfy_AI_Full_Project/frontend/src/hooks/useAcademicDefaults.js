import { useEffect, useState } from "react";
import { emptyAcademicContext } from "../components/subjects/AcademicContextFields";
import { getAcademicProfile, getAcademicStreams, getEducationLevels, getGrades, getSubject } from "../services/api";

export function useAcademicDefaults() {
  const [academic,setAcademic]=useState(emptyAcademicContext);
  useEffect(()=>{let active=true;async function load(){if(!localStorage.getItem("learnfy_token"))return;try{const {data:profile}=await getAcademicProfile();if(!profile.education_level_id)return;const [{data:levels},{data:grades},{data:streams},subjectResponse]=await Promise.all([getEducationLevels(),getGrades({level_id:profile.education_level_id}),getAcademicStreams(),profile.subject_ids?.[0]?getSubject(profile.subject_ids[0]):Promise.resolve({data:null})]);if(!active)return;const level=levels.find(item=>item.id===profile.education_level_id),grade=grades.find(item=>item.id===profile.grade_id),stream=streams.find(item=>item.id===profile.stream_id),subject=subjectResponse.data;setAcademic({educationLevelId:String(profile.education_level_id),levelCode:level?.code||"",gradeId:profile.grade_id?String(profile.grade_id):"",grade:grade?.name_en||"",medium:profile.medium||"",stream:stream?.name_en||"",streamId:profile.stream_id||null,subject:subject?.name_en||"",subjectId:subject?.id||null})}catch{/* Public pages and legacy profiles keep neutral filters. */}}load();return()=>{active=false}},[]);
  return [academic,setAcademic];
}
