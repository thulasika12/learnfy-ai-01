import { useEffect, useState } from "react";
import { FiCreditCard } from "react-icons/fi";
import Loader from "../../components/Loader";
import { getAdminPayments } from "../../services/api";

export default function PaymentAdministration() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    getAdminPayments().then(response => setItems(response.data))
      .catch(requestError => setError(requestError.response?.data?.detail || "Could not load transactions"))
      .finally(() => setLoading(false));
  }, []);
  return <div className="space-y-6">
    <div><h1 className="page-title flex items-center gap-2"><FiCreditCard />Payments & Premium Access</h1>
      <p className="mt-1 text-sm text-slate-500">Read-only PayHere and legacy Stripe transaction records.</p></div>
    {error && <div role="alert" className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/40 dark:text-red-200">{error}</div>}
    {loading ? <Loader /> : <div className="overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <div className="overflow-x-auto"><table className="w-full min-w-[1050px] text-left text-sm">
        <thead className="bg-slate-50 text-slate-500 dark:bg-slate-800"><tr>{["Order / Payment","User","Plan","Amount","Status","Provider","Transaction date","Access expiry"].map(label => <th key={label} className="px-4 py-3">{label}</th>)}</tr></thead>
        <tbody className="divide-y divide-slate-100 dark:divide-slate-800">{items.map(item => <tr key={item.order_id}>
          <td className="px-4 py-3"><p className="font-mono text-xs">{item.order_id}</p><p className="mt-1 font-mono text-xs text-slate-400">{item.provider_payment_id || "-"}</p></td>
          <td className="px-4 py-3"><p className="font-medium">{item.user_name}</p><p className="text-xs text-slate-500">{item.user_email}</p></td>
          <td className="px-4 py-3 capitalize">{item.plan_code.replaceAll("_", " ")}</td>
          <td className="px-4 py-3 font-medium">{item.currency} {Number(item.amount).toLocaleString()}</td>
          <td className="px-4 py-3"><span className="rounded bg-slate-100 px-2 py-1 text-xs font-semibold capitalize dark:bg-slate-800">{item.status}</span></td>
          <td className="px-4 py-3 capitalize">{item.provider}</td>
          <td className="px-4 py-3">{new Date(item.paid_at || item.created_at).toLocaleString()}</td>
          <td className="px-4 py-3">{item.subscription_expires_at ? new Date(item.subscription_expires_at).toLocaleDateString() : "-"}</td>
        </tr>)}</tbody></table></div>
      {!items.length && <p className="p-10 text-center text-slate-500">No payment transactions yet.</p>}
    </div>}
  </div>;
}
