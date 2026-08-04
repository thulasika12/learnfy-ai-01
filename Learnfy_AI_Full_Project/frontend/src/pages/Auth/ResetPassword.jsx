import { useState } from "react";
import { useNavigate, useSearchParams, Link } from "react-router-dom";
import toast from "react-hot-toast";
import { FiMail, FiKey, FiLock } from "react-icons/fi";

import { resetPassword } from "../../services/api";
import Button from "../../components/Button";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    email: searchParams.get("email") || "",
    reset_token: searchParams.get("token") || "",
    new_password: "",
    confirm_password: "",
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    const strongPassword = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$/;
    if (!form.email || !form.reset_token || !strongPassword.test(form.new_password)) {
      toast.error("Use 8+ characters with uppercase, lowercase, number, and symbol");
      return;
    }
    if (form.new_password !== form.confirm_password) {
      toast.error("Passwords do not match");
      return;
    }
    setLoading(true);
    try {
      await resetPassword({
        email: form.email.trim(),
        reset_token: form.reset_token.trim(),
        new_password: form.new_password,
        confirm_password: form.confirm_password,
      });
      toast.success("Password reset! Please log in.");
      navigate("/login");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Invalid or expired reset token");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-1">Reset your password</h2>
      <p className="text-slate-500 mb-6">Enter the reset code from your email along with a new password.</p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-600 mb-1 block">Email</label>
          <div className="relative">
            <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="email"
              className="input-field pl-10"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-600 mb-1 block">Reset Code</label>
          <div className="relative">
            <FiKey className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              className="input-field pl-10"
              value={form.reset_token}
              onChange={(e) => setForm({ ...form, reset_token: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-600 mb-1 block">New Password</label>
          <div className="relative">
            <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="password"
              className="input-field pl-10"
              placeholder="8+ chars with uppercase, lowercase, number, and symbol"
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
            />
          </div>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-600 mb-1 block">Confirm Password</label>
          <div className="relative">
            <FiLock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="password"
              className="input-field pl-10"
              placeholder="Re-enter the new password"
              value={form.confirm_password}
              onChange={(e) => setForm({ ...form, confirm_password: e.target.value })}
            />
          </div>
        </div>

        <Button type="submit" className="w-full" loading={loading}>
          Reset Password
        </Button>
      </form>

      <p className="text-center text-sm text-slate-500 mt-6">
        <Link to="/login" className="text-primary-600 font-semibold hover:underline">
          Back to login
        </Link>
      </p>
    </div>
  );
}
