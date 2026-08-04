import { useEffect, useState } from "react";

export default function ConfirmDialog({ open, title, message, confirmLabel, requireReason = true, danger = false, busy = false, onCancel, onConfirm }) {
  const [reason, setReason] = useState("");
  useEffect(() => { if (open) setReason(""); }, [open]);
  useEffect(() => { if (!open) return undefined; const close = (event) => event.key === "Escape" && !busy && onCancel(); document.addEventListener("keydown", close); return () => document.removeEventListener("keydown", close); }, [open, busy, onCancel]);
  if (!open) return null;
  const valid = !requireReason || reason.trim().length >= 3;
  return <div className="fixed inset-0 z-[70] flex items-center justify-center bg-slate-950/60 p-4" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && !busy && onCancel()}><section role="dialog" aria-modal="true" aria-labelledby="confirm-title" className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900"><h2 id="confirm-title" className="text-xl font-bold text-slate-900 dark:text-white">{title}</h2><p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{message}</p>{requireReason&&<label className="mt-5 block text-sm font-semibold">Reason<textarea autoFocus rows="3" maxLength="1000" className="input-field mt-2 resize-none" value={reason} onChange={(event)=>setReason(event.target.value)} /></label>}<div className="mt-6 flex justify-end gap-3"><button type="button" className="btn-secondary" disabled={busy} onClick={onCancel}>Cancel</button><button type="button" disabled={!valid||busy} className={danger?"inline-flex items-center justify-center rounded-lg bg-red-600 px-5 py-2.5 font-semibold text-white hover:bg-red-700 disabled:opacity-50":"btn-primary"} onClick={()=>onConfirm(reason.trim())}>{busy?"Working...":confirmLabel}</button></div></section></div>;
}
