import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { FiAward, FiCalendar, FiCreditCard } from "react-icons/fi";

import Loader from "../../components/Loader";
import { getMyPayments } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";

const statusClass = { success: "bg-emerald-100 text-emerald-700", pending: "bg-amber-100 text-amber-700", initiated: "bg-slate-100 text-slate-700", failed: "bg-red-100 text-red-700", cancelled: "bg-slate-100 text-slate-600", chargeback: "bg-red-100 text-red-700" };

export default function Subscription() {
  const { t } = usePreferences();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => { getMyPayments().then((res) => setData(res.data)).finally(() => setLoading(false)); }, []);
  if (loading) return <Loader />;

  return (
    <div className="space-y-7">
      <div><h1 className="page-title">{t("payments.premiumPayments")}</h1><p className="mt-2 text-slate-500">{t("payments.manageSubtitle")}</p></div>
      <section className="flex flex-col justify-between gap-6 rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900 sm:flex-row sm:items-center">
        <div className="flex items-start gap-4"><span className="flex h-12 w-12 items-center justify-center rounded-lg bg-amber-100 text-amber-600"><FiAward size={24} /></span><div><p className="text-sm text-slate-500">{t("payments.currentPlan")}</p><h2 className="text-2xl font-black capitalize text-slate-900 dark:text-white">{data?.plan_code} {data?.is_premium ? "Premium" : ""}</h2>{data?.subscription && <p className="mt-1 flex items-center gap-2 text-sm text-slate-500"><FiCalendar /> {t("payments.activeUntil")} {new Date(data.subscription.current_period_end).toLocaleDateString()}</p>}</div></div>
        <Link to="/pricing" className="btn-primary">{data?.is_premium ? t("payments.extendAccess") : t("payments.upgrade")}</Link>
      </section>
      <section>
        <h2 className="mb-4 flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white"><FiCreditCard /> {t("payments.recentPayments")}</h2>
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
          <table className="w-full min-w-[650px] text-left text-sm"><thead className="border-b border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-800"><tr><th className="px-5 py-3">{t("payments.date")}</th><th className="px-5 py-3">{t("payments.plan")}</th><th className="px-5 py-3">{t("payments.orderId")}</th><th className="px-5 py-3">{t("payments.amount")}</th><th className="px-5 py-3">{t("payments.status")}</th></tr></thead><tbody>
            {data?.payments.map((payment) => <tr key={payment.order_id} className="border-b border-slate-100 last:border-0 dark:border-slate-800"><td className="px-5 py-4 text-slate-600 dark:text-slate-300">{new Date(payment.created_at).toLocaleDateString()}</td><td className="px-5 py-4 font-medium capitalize dark:text-white">{payment.plan_code}</td><td className="px-5 py-4 font-mono text-xs text-slate-500">{payment.order_id}</td><td className="px-5 py-4 dark:text-white">{payment.currency} {Number(payment.amount).toLocaleString()}</td><td className="px-5 py-4"><span className={`rounded px-2 py-1 text-xs font-bold capitalize ${statusClass[payment.status] || statusClass.initiated}`}>{payment.status}</span></td></tr>)}
            {!data?.payments.length && <tr><td colSpan="5" className="px-5 py-10 text-center text-slate-500">{t("payments.noPayments")}</td></tr>}
          </tbody></table>
        </div>
      </section>
    </div>
  );
}
