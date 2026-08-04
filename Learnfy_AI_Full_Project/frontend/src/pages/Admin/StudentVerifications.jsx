import { useCallback, useEffect, useState } from "react";
import toast from "react-hot-toast";
import { FiCheck, FiDownload, FiX } from "react-icons/fi";

import ConfirmDialog from "../../components/ConfirmDialog";
import Loader from "../../components/Loader";
import {
  approveStudentVerification,
  getStudentVerificationDocument,
  getStudentVerifications,
  rejectStudentVerification,
} from "../../services/api";

export default function StudentVerifications() {
  const [filter, setFilter] = useState("pending");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState(null);
  const [decision, setDecision] = useState(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try { setItems((await getStudentVerifications(filter)).data); }
    catch (requestError) { setError(requestError.response?.data?.detail || "Could not load student verifications"); }
    finally { setLoading(false); }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  const viewDocument = async (item) => {
    try {
      const response = await getStudentVerificationDocument(item.id);
      const url = URL.createObjectURL(response.data);
      window.open(url, "_blank", "noopener,noreferrer");
      setTimeout(() => URL.revokeObjectURL(url), 60000);
    } catch (requestError) { toast.error(requestError.response?.data?.detail || "Could not open the document"); }
  };

  const decide = async (reason) => {
    setBusy(true);
    try {
      if (decision.action === "approve") await approveStudentVerification(decision.item.id);
      else await rejectStudentVerification(decision.item.id, reason);
      toast.success(decision.action === "approve" ? "Student verified" : "Verification rejected");
      setDecision(null); setSelected(null); load();
    } catch (requestError) { toast.error(requestError.response?.data?.detail || "Could not save the decision"); }
    finally { setBusy(false); }
  };

  return <div className="space-y-6">
    <div><h1 className="page-title">Student Verifications</h1><p className="mt-1 text-sm text-slate-500">Review student identity and enrolment documents securely.</p></div>
    <div className="flex flex-wrap gap-2">{["pending", "verified", "rejected"].map(value => <button key={value} className={filter === value ? "btn-primary" : "btn-secondary"} onClick={() => setFilter(value)}>{value[0].toUpperCase() + value.slice(1)}</button>)}</div>
    {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">{error}<button className="ml-3 font-semibold underline" onClick={load}>Retry</button></div>}
    {loading ? <Loader /> : items.length ? <div className="grid gap-4 lg:grid-cols-2">{items.map(item => <article key={item.id} className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900"><div className="flex items-start justify-between gap-4"><div><h2 className="font-bold text-slate-900 dark:text-white">{item.student_name}</h2><p className="text-sm text-slate-500">{item.student_email}</p></div><span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold capitalize dark:bg-slate-800">{item.status}</span></div><p className="mt-3 truncate text-sm text-slate-600 dark:text-slate-300">{item.original_filename}</p><p className="mt-1 text-xs text-slate-500">Submitted {new Date(item.submitted_at).toLocaleString()}</p>{item.rejection_reason && <p className="mt-3 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-200">{item.rejection_reason}</p>}<div className="mt-4 flex flex-wrap gap-2"><button className="btn-secondary" onClick={() => viewDocument(item)}><FiDownload />View document</button><button className="btn-secondary" onClick={() => setSelected(item)}>Details</button>{item.status === "pending" && <><button className="btn-primary" onClick={() => setDecision({ action: "approve", item })}><FiCheck />Approve</button><button className="btn-secondary text-red-600" onClick={() => setDecision({ action: "reject", item })}><FiX />Reject</button></>}</div></article>)}</div> : <div className="rounded-lg border border-slate-200 bg-white p-10 text-center text-slate-500 dark:border-slate-700 dark:bg-slate-900">No {filter} student verification requests.</div>}
    {selected && <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" onMouseDown={event => event.target === event.currentTarget && setSelected(null)}><section role="dialog" aria-modal="true" className="w-full max-w-lg rounded-lg bg-white p-6 dark:bg-slate-900"><div className="flex justify-between"><h2 className="text-xl font-bold">Student details</h2><button aria-label="Close" onClick={() => setSelected(null)}><FiX /></button></div><dl className="mt-5 grid grid-cols-[120px_1fr] gap-3 text-sm"><dt className="text-slate-500">Name</dt><dd>{selected.student_name}</dd><dt className="text-slate-500">Email</dt><dd className="break-all">{selected.student_email}</dd><dt className="text-slate-500">Document</dt><dd>{selected.original_filename}</dd><dt className="text-slate-500">Status</dt><dd className="capitalize">{selected.status}</dd><dt className="text-slate-500">Reviewed</dt><dd>{selected.reviewed_at ? new Date(selected.reviewed_at).toLocaleString() : "Not reviewed"}</dd></dl></section></div>}
    <ConfirmDialog open={!!decision} title={decision?.action === "approve" ? "Approve student verification?" : "Reject student verification?"} message="This decision updates the student's verification status and is recorded in the audit log." confirmLabel={decision?.action === "approve" ? "Approve student" : "Reject request"} requireReason={decision?.action === "reject"} danger={decision?.action === "reject"} busy={busy} onCancel={() => setDecision(null)} onConfirm={decide} />
  </div>;
}
