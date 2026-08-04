import { useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { FiMail } from "react-icons/fi";

import { forgotPassword } from "../../services/api";
import Button from "../../components/Button";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  const handleSubmit = async (ev) => {
    ev.preventDefault();
    if (!email) return toast.error("Enter your email address");
    setLoading(true);
    try {
      await forgotPassword({ email });
      setSent(true);
      toast.success("If that email exists, a reset link has been sent.");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-800 mb-1">Forgot password?</h2>
      <p className="text-slate-500 mb-6">
        Enter your email and we'll send you a link to reset your password.
      </p>

      {sent ? (
        <div className="glass-card p-4 text-sm text-slate-600">
          Check your email for a password reset link. You can also{" "}
          <Link to="/reset-password" className="text-primary-600 font-semibold hover:underline">
            enter your reset code here
          </Link>
          .
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Email</label>
            <div className="relative">
              <FiMail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="email"
                className="input-field pl-10"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
          </div>
          <Button type="submit" className="w-full" loading={loading}>
            Send Reset Link
          </Button>
        </form>
      )}

      <p className="text-center text-sm text-slate-500 mt-6">
        Remembered your password?{" "}
        <Link to="/login" className="text-primary-600 font-semibold hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
