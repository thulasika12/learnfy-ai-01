import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiBell, FiCheck, FiTrash2 } from "react-icons/fi";
import { deleteNotification, getNotifications, markAllNotificationsRead, markNotificationRead } from "../../services/api";

export default function Notifications() {
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const load = async () => {
    setLoading(true); setError("");
    try { const { data } = await getNotifications({ limit: 100 }); setItems(data.items); setUnread(data.unread_count); }
    catch { setError("Notifications could not be loaded."); }
    finally { setLoading(false); }
  };
  useEffect(() => { load(); }, []);
  const openItem = async (item) => {
    if (!item.is_read) {
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, is_read: true } : entry));
      setUnread((count) => Math.max(0, count - 1));
      try { await markNotificationRead(item.id); } catch { load(); return; }
    }
    if (typeof item.link === "string" && item.link.startsWith("/") && !item.link.startsWith("//")) navigate(item.link);
  };
  const markAll = async () => {
    setItems((current) => current.map((item) => ({ ...item, is_read: true }))); setUnread(0);
    try { await markAllNotificationsRead(); } catch { load(); }
  };
  const remove = async (event, item) => {
    event.stopPropagation();
    setItems((current) => current.filter((entry) => entry.id !== item.id));
    if (!item.is_read) setUnread((count) => Math.max(0, count - 1));
    try { await deleteNotification(item.id); } catch { load(); }
  };
  return <section className="mx-auto max-w-3xl">
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3"><div><h1 className="page-title">Notifications</h1><p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{unread} unread notification{unread === 1 ? "" : "s"}</p></div><button type="button" disabled={!unread} onClick={markAll} className="btn-secondary disabled:cursor-default disabled:opacity-50"><FiCheck /> Mark all as read</button></div>
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
      {loading && <p className="p-10 text-center text-slate-500" role="status">Loading notifications…</p>}
      {!loading && error && <div className="p-10 text-center"><p className="text-red-600" role="alert">{error}</p><button type="button" onClick={load} className="mt-3 font-semibold text-primary-600">Try again</button></div>}
      {!loading && !error && !items.length && <div className="p-12 text-center"><FiBell className="mx-auto mb-3 text-slate-300" size={36} /><p className="font-semibold text-slate-700 dark:text-slate-200">No notifications yet</p><p className="mt-1 text-sm text-slate-500">New activity will appear here.</p></div>}
      {!loading && !error && items.map((item) => <div key={item.id} role="button" tabIndex={0} onClick={() => openItem(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); openItem(item); } }} className={`flex cursor-pointer items-start gap-3 border-b border-slate-100 p-4 outline-none last:border-0 hover:bg-slate-50 focus:ring-2 focus:ring-inset focus:ring-primary-500 dark:border-slate-800 dark:hover:bg-slate-800 ${item.is_read ? "" : "bg-primary-50/60 dark:bg-primary-950/20"}`}>
        <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-primary-500" style={{ visibility: item.is_read ? "hidden" : "visible" }} aria-label={item.is_read ? undefined : "Unread"} /><span className="min-w-0 flex-1"><span className={`text-slate-900 dark:text-white ${item.is_read ? "font-medium" : "font-bold"}`}>{item.title}</span><span className="mt-1 block text-sm text-slate-500 dark:text-slate-400">{item.message}</span><time className="mt-2 block text-xs text-slate-400" dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time></span><button type="button" onClick={(event) => remove(event, item)} className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 focus:outline-none focus:ring-2 focus:ring-red-400" aria-label={`Delete ${item.title}`}><FiTrash2 /></button>
      </div>)}
    </div>
  </section>;
}
