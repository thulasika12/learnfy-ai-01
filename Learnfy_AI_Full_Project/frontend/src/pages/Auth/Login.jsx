import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import toast from "react-hot-toast";
import { FiMail, FiLock } from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import { usePreferences } from "../../hooks/usePreferences";
import Button from "../../components/Button";

export default function Login() {
  const { login } = useAuth();
  const { t } = usePreferences();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const e = {};
    if (!form.email) e.email = t("auth.emailRequired");
    if (!form.password) e.password = t("auth.passwordRequired");
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const loggedInUser = await login(form.email, form.password);
      toast.success(t("auth.welcome"));
      const dashboardByRole = {
        admin: "/admin/dashboard",
        teacher: "/teacher/dashboard",
        student: "/dashboard",
      };
      const queryNext = new URLSearchParams(location.search).get("next");
      const safeNext = queryNext?.startsWith("/") && !queryNext.startsWith("//") ? queryNext : null;
      const redirectTo = loggedInUser.role === "admin"
        ? "/admin/dashboard"
        : safeNext || location.state?.from?.pathname || dashboardByRole[loggedInUser.role] || "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || t("auth.invalidLogin"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-[1.75rem] border border-white/[0.08] bg-[#111827] p-6 shadow-[0_24px_80px_rgba(0,0,0,0.32)] sm:p-9 lg:p-10">
      <h2 className="mb-2 text-3xl font-extrabold tracking-tight text-white sm:text-4xl">{t("auth.welcomeBack")}</h2>
      <p className="mb-8 leading-7 text-[#CBD5E1]">{t("auth.loginSubtitle")}</p>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="mb-2 block text-sm font-semibold text-[#CBD5E1]">{t("auth.email")}</label>
          <div className="relative">
            <FiMail className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
            <input
              type="email"
              className="auth-login-input pl-11"
              placeholder="you@example.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
          {errors.email && <p className="text-xs text-red-500 mt-1">{errors.email}</p>}
        </div>

        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="text-sm font-semibold text-[#CBD5E1]">{t("auth.password")}</label>
            <Link to="/forgot-password" className="text-xs font-semibold text-[#60A5FA] transition-colors duration-300 hover:text-[#3B82F6] hover:underline active:text-[#2563EB]">
              {t("auth.forgotPassword")}
            </Link>
          </div>
          <div className="relative">
            <FiLock className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
            <input
              type="password"
              className="auth-login-input pl-11"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>
          {errors.password && <p className="text-xs text-red-500 mt-1">{errors.password}</p>}
        </div>

        <Button type="submit" className="auth-login-button mt-2 w-full" loading={loading}>
          {t("auth.login")}
        </Button>
      </form>

      <p className="mt-8 text-center text-sm text-[#CBD5E1]">
        {t("auth.noAccount")}{" "}
        <Link to="/register" className="font-semibold text-[#60A5FA] transition-colors duration-300 hover:text-[#3B82F6] hover:underline active:text-[#2563EB]">
          {t("auth.signUp")}
        </Link>
      </p>
    </div>
  );
}
