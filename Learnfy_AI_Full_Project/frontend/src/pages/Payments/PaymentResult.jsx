import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { FiCheckCircle, FiClock, FiXCircle } from "react-icons/fi";

import { getPaymentStatus } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";

const FINAL_STATUSES = new Set(["success", "failed", "cancelled", "chargeback"]);

export default function PaymentResult() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get("order_id");
  const returnedCancelled = searchParams.get("cancelled") === "1";
  const { t } = usePreferences();
  const [status, setStatus] = useState(returnedCancelled ? "cancelled" : "pending");
  const [payment, setPayment] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!orderId) { setError(t("payments.missingOrder")); return undefined; }
    let attempts = 0;
    let timer;
    const check = async () => {
      try {
        const response = await getPaymentStatus(orderId);
        const serverStatus = response.data.payment.status;
        setPayment(response.data.payment);
        setStatus(serverStatus === "initiated" ? (returnedCancelled ? "cancelled" : "pending") : serverStatus);
        if (!FINAL_STATUSES.has(serverStatus) && attempts < 10) {
          attempts += 1;
          timer = window.setTimeout(check, 2500);
        }
      } catch (err) {
        setError(err.response?.data?.detail || t("payments.verifyError"));
      }
    };
    check();
    return () => window.clearTimeout(timer);
  }, [orderId, returnedCancelled, t]);

  const success = status === "success";
  const pending = status === "pending" || status === "initiated";
  const Icon = success ? FiCheckCircle : pending ? FiClock : FiXCircle;
  const color = success ? "text-emerald-500" : pending ? "text-amber-500" : "text-red-500";

  return (
    <div className="mx-auto max-w-xl py-10 text-center">
      <div className="rounded-lg border border-slate-200 bg-white p-8 dark:border-slate-700 dark:bg-slate-900">
        <Icon className={`mx-auto ${color}`} size={58} />
        <h1 className="mt-5 text-2xl font-black text-slate-900 dark:text-white">
          {success ? t("payments.successTitle") : pending ? t("payments.pendingTitle") : status === "cancelled" ? t("payments.cancelledTitle") : t("payments.failedTitle")}
        </h1>
        <p className="mt-3 text-slate-500 dark:text-slate-300">
          {success ? t("payments.successMessage") : pending ? t("payments.pendingMessage") : status === "cancelled" ? t("payments.cancelledMessage") : t("payments.failedMessage")}
        </p>
        {error && <p className="mt-4 rounded bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">{error}</p>}
        {payment && <dl className="mt-6 grid grid-cols-2 gap-3 border-t border-slate-100 pt-5 text-left text-sm dark:border-slate-700"><dt className="text-slate-500">{t("payments.orderId")}</dt><dd className="break-all text-right font-medium dark:text-white">{payment.order_id}</dd><dt className="text-slate-500">{t("payments.amount")}</dt><dd className="text-right font-medium dark:text-white">{payment.currency} {Number(payment.amount).toLocaleString()}</dd></dl>}
        <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row"><Link to="/payments" className="btn-primary">{t("payments.viewSubscription")}</Link>{!success && <Link to="/pricing" className="btn-secondary">{t("payments.tryAgain")}</Link>}</div>
      </div>
    </div>
  );
}
