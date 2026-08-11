import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { FiArrowLeft, FiExternalLink, FiLock } from "react-icons/fi";
import toast from "react-hot-toast";

import Button from "../../components/Button";
import Loader from "../../components/Loader";
import { createPaymentCheckout, getPaymentPlans, normalizePaymentPlans } from "../../services/api";
import { usePreferences } from "../../hooks/usePreferences";

export default function Checkout() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t } = usePreferences();
  const planCode = searchParams.get("plan");
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [billing, setBilling] = useState({ phone: "", address: "", city: "" });

  useEffect(() => {
    getPaymentPlans().then((res) => {
      const selected = normalizePaymentPlans(res.data).find((item) => item.code === planCode && item.code !== "free");
      if (!selected) navigate("/pricing", { replace: true });
      setPlan(selected);
    }).catch(() => toast.error(t("payments.loadError"))).finally(() => setLoading(false));
  }, [navigate, planCode, t]);

  const submit = async (event) => {
    event.preventDefault();
    if (submitting || !plan) return;
    setSubmitting(true);
    try {
      const response = await createPaymentCheckout({ plan_code: plan.code, ...billing });
      const form = document.createElement("form");
      form.method = "POST"; form.action = response.data.checkout_url;
      Object.entries(response.data.fields).forEach(([name, value]) => {
        const input = document.createElement("input"); input.type = "hidden"; input.name = name; input.value = value;
        form.appendChild(input);
      });
      document.body.appendChild(form); form.submit();
    } catch (error) {
      toast.error(error.response?.data?.detail || t("payments.checkoutError"));
      setSubmitting(false);
    }
  };

  if (loading || !plan) return <Loader />;
  return (
    <div className="mx-auto max-w-4xl">
      <Link to="/pricing" className="mb-6 inline-flex items-center gap-2 text-sm font-semibold text-primary-600"><FiArrowLeft /> {t("payments.backToPlans")}</Link>
      <div className="grid overflow-hidden rounded-lg border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900 lg:grid-cols-[.85fr_1.15fr]">
        <aside className="bg-slate-900 p-7 text-white lg:p-9">
          <p className="text-sm font-semibold text-cyan-300">{t("payments.orderSummary")}</p>
          <h1 className="mt-3 text-2xl font-black">{plan.name}</h1>
          <p className="mt-5 text-4xl font-black">LKR {Number(plan.amount).toLocaleString()}</p>
          <p className="mt-1 text-sm text-slate-300">{plan.duration_days} {t("payments.daysAccess")}</p>
          <div className="mt-8 border-t border-slate-700 pt-6 text-sm leading-6 text-slate-300"><FiLock className="mb-3 text-emerald-400" />{t("payments.cardOnStripe")}</div>
        </aside>
        <form onSubmit={submit} className="space-y-5 p-7 lg:p-9">
          <div><h2 className="text-xl font-bold text-slate-900 dark:text-white">{t("payments.billingDetails")}</h2><p className="mt-1 text-sm text-slate-500">{t("payments.billingSubtitle")}</p></div>
          <label className="block text-sm font-medium dark:text-slate-200">{t("payments.phone")}<input required minLength="7" maxLength="30" className="input-field mt-1" value={billing.phone} onChange={(event) => setBilling({...billing, phone:event.target.value})} /></label>
          <label className="block text-sm font-medium dark:text-slate-200">{t("payments.address")}<input required minLength="3" maxLength="255" className="input-field mt-1" value={billing.address} onChange={(event) => setBilling({...billing, address:event.target.value})} /></label>
          <label className="block text-sm font-medium dark:text-slate-200">{t("payments.city")}<input required minLength="2" maxLength="100" className="input-field mt-1" value={billing.city} onChange={(event) => setBilling({...billing, city:event.target.value})} /></label>
          <Button type="submit" disabled={submitting} loading={submitting} className="w-full">{t("payments.continueStripe")} <FiExternalLink /></Button>
          <p className="text-center text-xs text-slate-500">{t("payments.noCardStorage")}</p>
        </form>
      </div>
    </div>
  );
}
