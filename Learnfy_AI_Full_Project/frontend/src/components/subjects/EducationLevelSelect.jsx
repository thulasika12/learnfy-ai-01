import { useEffect, useState } from "react";
import { getEducationLevels } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";
export default function EducationLevelSelect({ value, onChange, className="input-field", ...props }) {
  const { language } = usePreferences(); const [items,setItems]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState("");
  useEffect(()=>{let active=true;setLoading(true);setError("");getEducationLevels().then(r=>{if(active)setItems(Array.isArray(r.data)?r.data:r.data?.items||[]);}).catch(error=>{if(active){setItems([]);setError(error.response?.data?.detail||"Could not load education levels");}}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]);
  return <div><select className={className} value={value} disabled={loading} onChange={e=>{const item=items.find(x=>String(x.id)===e.target.value);onChange(e.target.value,item);}} {...props}><option value="">{loading?"Loading education levels…":"Select education level"}</option>{items.map(x=><option key={x.id} value={x.id}>{x[`name_${language}`]||x.name_en}</option>)}</select>{error&&<p className="mt-1 text-xs text-red-500" role="alert">{error}</p>}{!loading&&!error&&!items.length&&<p className="mt-1 text-xs text-slate-500">No options available</p>}</div>;
}
