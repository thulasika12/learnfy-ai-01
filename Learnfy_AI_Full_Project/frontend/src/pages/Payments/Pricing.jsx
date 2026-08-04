import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiCheck, FiShield } from "react-icons/fi";

import { getPaymentPlans } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";
import { usePreferences } from "../../hooks/usePreferences";
import Loader from "../../components/Loader";

export default function Pricing() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const { isAuthenticated } = useAuth();
  const { t } = usePreferences();
  const navigate = useNavigate();

  useEffect(() => {
    getPaymentPlans().then((res) => setPlans(res.data)).finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader />;

  const choosePlan = (plan) => {
    if (plan.code === "free") return navigate(isAuthenticated ? "/dashboard" : "/register");
    navigate(isAuthenticated ? `/payments/checkout?plan=${plan.code}` : `/login?next=${encodeURIComponent(`/payments/checkout?plan=${plan.code}`)}`);
  };

  return (
    <div className="mx-auto max-w-6xl px-5 py-14 md:py-20">
      <div className="mx-auto max-w-2xl text-center">
        <h1 className="text-3xl font-black text-slate-900 dark:text-white md:text-5xl">{t("payments.pricingTitle")}</h1>
        <p className="mt-4 text-lg text-slate-500 dark:text-slate-300">{t("payments.pricingSubtitle")}</p>
      </div>
      <div className="mt-12 grid gap-6 md:grid-cols-3">
        {plans.map((plan) => (
          <section key={plan.code} className={`relative rounded-lg border bg-white p-7 dark:bg-slate-900 ${plan.code === "yearly" ? "border-emerald-500 shadow-lg" : "border-slate-200 dark:border-slate-700"}`}>
            {plan.code === "yearly" && <span className="absolute right-4 top-4 rounded bg-emerald-100 px-2 py-1 text-xs font-bold text-emerald-700">{t("payments.bestValue")}</span>}
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">{plan.name}</h2>
            <div className="mt-5 flex items-end gap-2">
              <span className="text-4xl font-black text-slate-900 dark:text-white">LKR {Number(plan.amount).toLocaleString()}</span>
              {plan.duration_days && <span className="pb-1 text-sm text-slate-500">/ {plan.duration_days} {t("payments.days")}</span>}
            </div>
            <ul className="mt-7 min-h-32 space-y-3">
              {plan.features.map((feature) => <li key={feature} className="flex gap-3 text-sm text-slate-600 dark:text-slate-300"><FiCheck className="mt-0.5 shrink-0 text-emerald-500" />{feature}</li>)}
            </ul>
            <button onClick={() => choosePlan(plan)} className={`mt-7 w-full ${plan.code === "free" ? "btn-secondary" : "btn-primary"}`}>
              {plan.code === "free" ? t("payments.startFree") : t("payments.choosePlan")}
            </button>
          </section>
        ))}
      </div>
      <p className="mt-8 flex items-center justify-center gap-2 text-center text-sm text-slate-500 dark:text-slate-400"><FiShield /> {t("payments.secureNotice")}</p>
    </div>
  );
}
