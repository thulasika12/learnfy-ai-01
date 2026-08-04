import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  FiBell,
  FiGlobe,
  FiLogOut,
  FiMoon,
  FiShield,
  FiTrash2,
  FiUser,
} from "react-icons/fi";

import { useAuth } from "../../hooks/useAuth";
import { usePreferences } from "../../hooks/usePreferences";
import { changePassword, deleteAccount, updateProfile } from "../../services/api";
import Card from "../../components/Card";
import Button from "../../components/Button";

export default function Settings() {
  const { user, updateUserCache, logout } = useAuth();
  const { theme, setTheme, language, setLanguage, t } = usePreferences();
  const navigate = useNavigate();
  const [name, setName] = useState(user?.name || "");
  const [saving, setSaving] = useState(false);
  const [notifications, setNotifications] = useState({ email: true, aiTips: true, groupActivity: false });
  const [passwords, setPasswords] = useState({ current: "", next: "", confirm: "" });
  const [changingPassword, setChangingPassword] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleting, setDeleting] = useState(false);

  const handleSaveName = async () => {
    setSaving(true);
    try {
      const res = await updateProfile({ name });
      updateUserCache(res.data);
      toast.success(t("settings.nameUpdated"));
    } catch (err) {
      toast.error(err.response?.data?.detail || t("settings.couldNotSave"));
    } finally {
      setSaving(false);
    }
  };

  const toggle = (key) => setNotifications((n) => ({ ...n, [key]: !n[key] }));

  const handleChangePassword = async (event) => {
    event.preventDefault();
    if (passwords.next !== passwords.confirm) return toast.error(t("settings.passwordMismatch"));
    setChangingPassword(true);
    try {
      await changePassword({
        current_password: passwords.current,
        new_password: passwords.next,
        confirm_password: passwords.confirm,
      });
      setPasswords({ current: "", next: "", confirm: "" });
      toast.success(t("settings.passwordChanged"));
    } catch (err) {
      toast.error(err.response?.data?.detail || t("settings.couldNotChangePassword"));
    } finally {
      setChangingPassword(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) return toast.error(t("settings.enterPassword"));
    if (!window.confirm(t("settings.deleteConfirm"))) return;
    setDeleting(true);
    try {
      await deleteAccount({ password: deletePassword });
      await logout(false);
      navigate("/register", { replace: true });
      toast.success(t("settings.accountDeleted"));
    } catch (err) {
      toast.error(err.response?.data?.detail || t("settings.couldNotDelete"));
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="page-title">{t("settings.title")}</h1>

      {user?.role === "student" && <Card><h3 className="font-bold text-slate-800 dark:text-white">{t("teacher.applyTitle")}</h3><p className="my-2 text-sm text-slate-500">{t("teacher.applySubtitle")}</p><Link to="/teacher-verification" className="btn-primary inline-flex">{t("sidebar.applyTeacher")}</Link></Card>}

      <Card>
        <h3 className="mb-4 flex items-center gap-2 font-bold text-slate-800">
          <FiGlobe /> {t("settings.appearanceLanguage")}
        </h3>
        <div className="grid gap-5 sm:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-600">
              <FiMoon className="mr-1 inline" /> {t("settings.theme")}
            </label>
            <div className="grid grid-cols-2 gap-2">
              {["light", "dark"].map((value) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setTheme(value)}
                  className={`rounded-xl border px-4 py-2.5 text-sm font-semibold transition ${
                    theme === value
                      ? "border-primary-500 bg-primary-50 text-primary-700 dark:bg-primary-950/50 dark:text-primary-200"
                      : "border-slate-200 text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:hover:bg-slate-800"
                  }`}
                >
                  {t(`theme.${value}`)}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-600">
              {t("settings.language")}
            </label>
            <select
              className="input-field"
              value={language}
              onChange={(event) => setLanguage(event.target.value)}
            >
              <option value="en">{t("language.english")}</option>
              <option value="ta">{t("language.tamil")}</option>
              <option value="si">{t("language.sinhala")}</option>
            </select>
          </div>
        </div>
      </Card>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
          <FiUser /> {t("settings.accountDetails")}
        </h3>
        <label className="text-sm font-medium text-slate-600 mb-1 block">
          {t("settings.fullName")}
        </label>
        <input className="input-field mb-3" value={name} onChange={(e) => setName(e.target.value)} />
        <label className="text-sm font-medium text-slate-600 mb-1 block">
          {t("settings.email")}
        </label>
        <input className="input-field mb-4 bg-slate-100" value={user?.email} disabled />
        <Button onClick={handleSaveName} loading={saving}>
          {t("settings.saveChanges")}
        </Button>
      </Card>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
          <FiBell /> {t("settings.notifications")}
        </h3>
        <div className="space-y-3">
          {[
            { key: "email", label: t("settings.emailNotifications") },
            { key: "aiTips", label: t("settings.aiTips") },
            { key: "groupActivity", label: t("settings.groupActivity") },
          ].map((item) => (
            <label key={item.key} className="flex items-center justify-between text-sm text-slate-600">
              {item.label}
              <input
                type="checkbox"
                checked={notifications[item.key]}
                onChange={() => toggle(item.key)}
                className="w-4 h-4 accent-primary-600"
              />
            </label>
          ))}
        </div>
      </Card>

      <Card>
        <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
          <FiShield /> {t("settings.privacy")}
        </h3>
        <form onSubmit={handleChangePassword} className="space-y-3">
          <input
            type="password"
            className="input-field"
            placeholder={t("settings.currentPassword")}
            value={passwords.current}
            onChange={(event) => setPasswords({ ...passwords, current: event.target.value })}
          />
          <input
            type="password"
            className="input-field"
            placeholder={t("settings.newPassword")}
            value={passwords.next}
            onChange={(event) => setPasswords({ ...passwords, next: event.target.value })}
          />
          <input
            type="password"
            className="input-field"
            placeholder={t("settings.confirmPassword")}
            value={passwords.confirm}
            onChange={(event) => setPasswords({ ...passwords, confirm: event.target.value })}
          />
          <Button type="submit" loading={changingPassword}>
            {t("settings.changePassword")}
          </Button>
        </form>
        <div className="my-5 border-t border-slate-100" />
        <Button
          variant="secondary"
          className="text-red-600 border-red-200 hover:bg-red-50"
          onClick={async () => {
            await logout();
            navigate("/login");
          }}
        >
          <FiLogOut /> {t("settings.logoutDevice")}
        </Button>
      </Card>

      <Card className="border border-red-100">
        <h3 className="font-bold text-red-700 mb-2 flex items-center gap-2">
          <FiTrash2 /> {t("settings.deleteAccount")}
        </h3>
        <p className="mb-3 text-sm text-slate-500">{t("settings.deleteDescription")}</p>
        <input
          type="password"
          className="input-field mb-3"
          placeholder={t("settings.confirmCurrentPassword")}
          value={deletePassword}
          onChange={(event) => setDeletePassword(event.target.value)}
        />
        <Button
          variant="secondary"
          className="text-red-600 border-red-200 hover:bg-red-50"
          loading={deleting}
          onClick={handleDeleteAccount}
        >
          {t("settings.deleteMyAccount")}
        </Button>
      </Card>
    </div>
  );
}
