import { useEffect, useState } from "react";
import { getAcademicStreams } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";

export const AL_STREAMS = ["Biological Science", "Physical Science", "Commerce", "Arts", "Engineering Technology", "Bio Systems Technology", "General/Common Subjects"];

export default function StreamSelect({ value, onChange, className = "input-field", includeAll = false, ...props }) {
  const [items,setItems]=useState([]); const [loading,setLoading]=useState(true); const [error,setError]=useState(""); const { language }=usePreferences();
  useEffect(()=>{let active=true;setLoading(true);setError("");getAcademicStreams().then(response=>{if(active)setItems(Array.isArray(response.data)?response.data:response.data?.items||[]);}).catch(error=>{if(active){setItems([]);setError(error.response?.data?.detail||"Could not load streams");}}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]);
  const options=items.map(item=>({value:item.name_en,label:item[`name_${language}`]||item.name_en,item}));
  return <div><select disabled={loading} className={className} value={value} onChange={(event) => { const entry=options.find(x=>x.value===event.target.value); onChange(event.target.value,entry?.item); }} {...props}>
    {includeAll && <option value="">All streams</option>}
    {!includeAll && <option value="">Select a stream</option>}
    {options.map((entry) => <option key={entry.value} value={entry.value}>{entry.label}</option>)}
  </select>{error&&<p className="mt-1 text-xs text-red-500" role="alert">{error}</p>}{!loading&&!error&&!items.length&&<p className="mt-1 text-xs text-slate-500">No options available</p>}</div>;
}
