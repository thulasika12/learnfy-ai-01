import { useEffect, useState } from "react";
import { getGrades } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";
export default function GradeSelect({ levelId, value, onChange, className="input-field", ...props }) {
  const { language }=usePreferences(); const [items,setItems]=useState([]); const [loading,setLoading]=useState(false); const [error,setError]=useState("");
  useEffect(()=>{let active=true;if(!levelId){setItems([]);setError("");return()=>{active=false;};}setLoading(true);setError("");getGrades({level_id:levelId}).then(r=>{if(active)setItems(Array.isArray(r.data)?r.data:r.data?.items||[]);}).catch(error=>{if(active){setItems([]);setError(error.response?.data?.detail||"Could not load grades");}}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[levelId]);
  return <div><select disabled={!levelId||loading} className={className} value={value} onChange={e=>{const item=items.find(x=>String(x.id)===e.target.value);onChange(e.target.value,item);}} {...props}><option value="">{loading?"Loading grades…":"Select grade"}</option>{items.map(x=><option key={x.id} value={x.id}>{x[`name_${language}`]||x.name_en}</option>)}</select>{error&&<p className="mt-1 text-xs text-red-500" role="alert">{error}</p>}{levelId&&!loading&&!error&&!items.length&&<p className="mt-1 text-xs text-slate-500">No options available</p>}</div>;
}
