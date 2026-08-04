import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import {
  FiAlertCircle,
  FiArrowLeft,
  FiCheckCircle,
  FiClock,
  FiFileText,
  FiRefreshCw,
  FiShield,
  FiUploadCloud,
} from "react-icons/fi";

import Button from "../../components/Button";
import Card from "../../components/Card";
import Loader from "../../components/Loader";
import { useAuth } from "../../hooks/useAuth";
import { usePreferences } from "../../hooks/usePreferences";
import { getMyStudentVerification, submitStudentVerification } from "../../services/api";

const ALLOWED_TYPES = ["application/pdf", "image/jpeg", "image/png"];
const MAX_FILE_SIZE = 5 * 1024 * 1024;

function StatusScreen({ icon, iconClass, title, message, children }) {
  return (
    <div className="mx-auto max-w-3xl py-4 sm:py-8">
      <Card hover={false} className="p-6 text-center sm:p-10">
        <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${iconClass}`}>
          {icon}
        </div>
        <h1 className="mt-5 text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">{title}</h1>
        <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">{message}</p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">{children}</div>
      </Card>
    </div>
  );
}

export default function StudentVerification() {
  const { user } = useAuth();
  const { t } = usePreferences();
  const fileInputRef = useRef(null);
  const [verification, setVerification] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [submitError, setSubmitError] = useState("");
  const [file, setFile] = useState(null);
  const [saving, setSaving] = useState(false);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setLoadError("");
    try {
      const response = await getMyStudentVerification();
      setVerification(response.data ?? { status: "unverified" });
    } catch (error) {
      setLoadError(error.response?.data?.detail || t("studentVerification.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const selectFile = (event) => {
    const selected = event.target.files?.[0] ?? null;
    setSubmitError("");
    if (selected && (!ALLOWED_TYPES.includes(selected.type) || selected.size > MAX_FILE_SIZE)) {
      setFile(null);
      event.target.value = "";
      setSubmitError(t("studentVerification.invalidFile"));
      return;
    }
    setFile(selected);
  };

  const submit = async (event) => {
    event.preventDefault();
    if (!file) {
      setSubmitError(t("studentVerification.documentRequired"));
      return;
    }
    setSaving(true);
    setSubmitError("");
    const data = new FormData();
    data.append("proof", file);
    try {
      const response = await submitStudentVerification(data);
      setVerification(response.data);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
      toast.success(t("studentVerification.submitted"));
    } catch (error) {
      setSubmitError(error.response?.data?.detail || t("studentVerification.submitFailed"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <Loader full label={t("studentVerification.loading")} />;

  if (loadError) {
    return (
      <StatusScreen
        icon={<FiAlertCircle size={30} />}
        iconClass="bg-red-100 text-red-600 dark:bg-red-950/50 dark:text-red-300"
        title={t("studentVerification.loadErrorTitle")}
        message={loadError}
      >
        <button type="button" className="btn-primary" onClick={loadStatus}><FiRefreshCw />{t("studentVerification.retry")}</button>
        <Link className="btn-secondary" to="/dashboard"><FiArrowLeft />{t("studentVerification.backDashboard")}</Link>
      </StatusScreen>
    );
  }

  if (user?.role !== "student") {
    return (
      <StatusScreen
        icon={<FiAlertCircle size={30} />}
        iconClass="bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300"
        title={t("studentVerification.studentsOnlyTitle")}
        message={t("studentVerification.studentsOnlyMessage")}
      >
        <Link className="btn-primary" to="/dashboard"><FiArrowLeft />{t("studentVerification.backDashboard")}</Link>
      </StatusScreen>
    );
  }

  if (verification?.status === "verified") {
    return (
      <StatusScreen
        icon={<FiCheckCircle size={34} />}
        iconClass="bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300"
        title={t("studentVerification.verifiedTitle")}
        message={t("studentVerification.verifiedMessage")}
      >
        <Link className="btn-primary" to="/dashboard">{t("studentVerification.backDashboard")}</Link>
        <Link className="btn-secondary" to="/profile">{t("studentVerification.viewProfile")}</Link>
      </StatusScreen>
    );
  }

  if (verification?.status === "pending") {
    return (
      <StatusScreen
        icon={<FiClock size={32} />}
        iconClass="bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300"
        title={t("studentVerification.pendingTitle")}
        message={t("studentVerification.pendingMessage")}
      >
        <Link className="btn-primary" to="/dashboard"><FiArrowLeft />{t("studentVerification.backDashboard")}</Link>
      </StatusScreen>
    );
  }

  return (
    <div className="mx-auto max-w-4xl space-y-6 pb-8">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
        <div>
          <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-primary-600 dark:text-primary-300"><FiShield />Learnfy AI</div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white sm:text-3xl">{t("studentVerification.title")}</h1>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">{t("studentVerification.subtitle")}</p>
        </div>
        <Link className="btn-secondary shrink-0" to="/dashboard"><FiArrowLeft />{t("studentVerification.backDashboard")}</Link>
      </div>

      {verification?.status === "rejected" && (
        <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-200">
          <div className="flex gap-3"><FiAlertCircle className="mt-0.5 shrink-0" size={20} /><div><h2 className="font-bold">{t("studentVerification.rejectedTitle")}</h2><p className="mt-1 text-sm">{verification.rejection_reason || t("studentVerification.rejectedMessage")}</p><p className="mt-2 text-xs">{t("studentVerification.resubmitMessage")}</p></div></div>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[1fr_0.7fr]">
        <Card hover={false} className="p-5 sm:p-7">
          <div className="flex items-start gap-3"><div className="rounded-lg bg-primary-50 p-2.5 text-primary-700 dark:bg-slate-800 dark:text-primary-300"><FiUploadCloud size={23} /></div><div><h2 className="text-lg font-bold text-slate-900 dark:text-white">{t("studentVerification.uploadTitle")}</h2><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{t("studentVerification.uploadSubtitle")}</p></div></div>
          <form onSubmit={submit} className="mt-6 space-y-4">
            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-200">
              {t("studentVerification.document")}
              <input ref={fileInputRef} required type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" className="input-field mt-2 file:mr-3 file:rounded-lg file:border-0 file:bg-primary-50 file:px-3 file:py-2 file:font-semibold file:text-primary-700 dark:file:bg-slate-700 dark:file:text-primary-200" onChange={selectFile} />
            </label>
            <p className="text-xs leading-5 text-slate-500 dark:text-slate-400">{t("studentVerification.documentHelp")}</p>
            {file && <div className="flex items-center gap-2 rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:bg-slate-800 dark:text-slate-200"><FiFileText className="shrink-0" /><span className="min-w-0 truncate">{file.name}</span></div>}
            {submitError && <p role="alert" className="flex items-start gap-2 text-sm text-red-600 dark:text-red-300"><FiAlertCircle className="mt-0.5 shrink-0" />{submitError}</p>}
            <Button type="submit" loading={saving} disabled={!file} className="w-full sm:w-auto">{verification?.status === "rejected" ? t("studentVerification.resubmit") : t("studentVerification.submit")}</Button>
          </form>
        </Card>

        <aside className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900 sm:p-6">
          <h2 className="font-bold text-slate-900 dark:text-white">{t("studentVerification.statusTitle")}</h2>
          <div className="mt-4 flex items-center gap-3"><span className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"><FiShield /></span><div><p className="text-xs uppercase text-slate-500 dark:text-slate-400">{t("studentVerification.currentStatus")}</p><p className="font-semibold capitalize text-slate-900 dark:text-white">{t(`studentVerification.status.${verification?.status || "unverified"}`)}</p></div></div>
          <div className="mt-5 border-t border-slate-200 pt-5 text-sm leading-6 text-slate-600 dark:border-slate-700 dark:text-slate-300">{t("studentVerification.privacy")}</div>
        </aside>
      </div>
    </div>
  );
}
