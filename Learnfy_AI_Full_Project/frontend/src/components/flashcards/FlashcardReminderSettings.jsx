import { useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { FiBell, FiBellOff } from "react-icons/fi";

import { getFlashcardReminder, updateFlashcardReminder } from "../../services/api";

export default function FlashcardReminderSettings() {
  const [enabled, setEnabled] = useState(false); const [time, setTime] = useState("20:00"); const [loading, setLoading] = useState(false);
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  useEffect(() => { getFlashcardReminder().then((res) => { if (res.data) { setEnabled(res.data.is_enabled); setTime(String(res.data.reminder_time).slice(0, 5)); } }); }, []);
  const next = useMemo(() => { if (!enabled) return null; const [hour, minute] = time.split(":").map(Number); const date = new Date(); date.setHours(hour, minute, 0, 0); if (date <= new Date()) date.setDate(date.getDate() + 1); return date; }, [enabled, time]);
  useEffect(() => { if (!next) return undefined; const delay = next.getTime() - Date.now(); const timer = window.setTimeout(() => { if (Notification.permission === "granted") new Notification("Learnfy AI revision", { body: "Your daily flashcard revision is ready." }); else toast("Your daily flashcard revision is ready."); }, delay); return () => window.clearTimeout(timer); }, [next]);
  const save = async (nextEnabled) => { setLoading(true); try { if (nextEnabled && "Notification" in window && Notification.permission === "default") await Notification.requestPermission(); await updateFlashcardReminder({ is_enabled: nextEnabled, reminder_time: `${time}:00`, timezone }); setEnabled(nextEnabled); toast.success(nextEnabled ? "Daily reminder enabled" : "Reminder disabled"); } catch { toast.error("Could not update reminder"); } finally { setLoading(false); } };
  return <section className="rounded-lg border border-slate-200 bg-white p-5 dark:border-slate-700 dark:bg-slate-900"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><h2 className="flex items-center gap-2 font-bold text-slate-900 dark:text-white">{enabled ? <FiBell /> : <FiBellOff />} Daily revision reminder</h2><p className="mt-1 text-sm text-slate-500">{next ? `Next revision: ${next.toLocaleString()}` : "Enable a browser or in-app revision reminder."}</p></div><div className="flex items-center gap-2"><input type="time" aria-label="Reminder time" className="input-field w-32" value={time} onChange={(e) => setTime(e.target.value)} /><button disabled={loading} className={enabled ? "btn-secondary" : "btn-primary"} onClick={() => save(!enabled)}>{enabled ? "Disable" : "Enable"}</button></div></div></section>;
}
