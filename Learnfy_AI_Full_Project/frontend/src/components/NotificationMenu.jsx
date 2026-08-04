import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { FiBell, FiCheck, FiMessageCircle, FiTrash2, FiUsers, FiZap } from "react-icons/fi";
import { deleteNotification, getNotifications, markAllNotificationsRead, markNotificationRead } from "../services/api";

const icons = { group: FiUsers, reminder: FiBell, quiz: FiZap, reply: FiMessageCircle };
const relativeTime = (value) => {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 1000));
  if (seconds < 60) return "Just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return new Date(value).toLocaleDateString();
};

export default function NotificationMenu() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const rootRef = useRef(null);
  const navigate = useNavigate();

  const load = useCallback(async (showLoading = true) => {
    if (showLoading) setLoading(true);
    setError("");
    try {
      const { data } = await getNotifications({ limit: 10 });
      setItems(data.items);
      setUnread(data.unread_count);
    } catch {
      setError("Notifications could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(false); }, [load]);
  useEffect(() => {
    if (!open) return undefined;
    load();
    const onPointerDown = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const onKeyDown = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open, load]);

  const selectItem = async (item) => {
    if (!item.is_read) {
      setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, is_read: true } : entry));
      setUnread((count) => Math.max(0, count - 1));
      try { await markNotificationRead(item.id); } catch { load(false); }
    }
    setOpen(false);
    if (typeof item.link === "string" && item.link.startsWith("/") && !item.link.startsWith("//")) navigate(item.link);
  };

  const markAll = async () => {
    if (!unread) return;
    setItems((current) => current.map((item) => ({ ...item, is_read: true })));
    setUnread(0);
    try { await markAllNotificationsRead(); } catch { setError("Could not mark notifications as read."); load(false); }
  };

  const remove = async (event, item) => {
    event.stopPropagation();
    setItems((current) => current.filter((entry) => entry.id !== item.id));
    if (!item.is_read) setUnread((count) => Math.max(0, count - 1));
    try { await deleteNotification(item.id); } catch { setError("Could not delete the notification."); load(false); }
  };

  return (
    <div className="relative" ref={rootRef}>
      <button type="button" onClick={(event) => { event.stopPropagation(); setOpen((value) => !value); }}
        aria-label="Notifications" aria-haspopup="menu" aria-expanded={open} aria-controls="notification-dropdown"
        className="relative cursor-pointer rounded-lg p-2 text-slate-500 hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 dark:text-slate-300 dark:hover:bg-slate-800 dark:focus-visible:ring-offset-slate-900">
        <FiBell size={20} />
        {unread > 0 && <span className="absolute -right-1 -top-1 min-w-[1.15rem] rounded-full bg-red-500 px-1 text-center text-[10px] font-bold leading-[1.15rem] text-white" aria-label={`${unread} unread notifications`}>{unread > 9 ? "9+" : unread}</span>}
      </button>

      {open && <section id="notification-dropdown" role="menu" aria-label="Notifications"
        className="fixed left-3 right-3 top-16 z-[100] mt-2 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900 sm:absolute sm:left-auto sm:right-0 sm:top-full sm:w-[23rem]">
        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3 dark:border-slate-700">
          <div><h2 className="font-bold text-slate-900 dark:text-white">Notifications</h2><p className="text-xs text-slate-500 dark:text-slate-400">{unread} unread</p></div>
          <button type="button" onClick={markAll} disabled={!unread} className="rounded-md px-2 py-1 text-xs font-semibold text-primary-600 hover:bg-primary-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 disabled:cursor-default disabled:opacity-50 dark:text-primary-300 dark:hover:bg-slate-800"><FiCheck className="inline" /> Mark all as read</button>
        </div>
        <div className="max-h-[min(26rem,calc(100vh-9rem))] overflow-y-auto">
          {loading && <div className="p-8 text-center text-sm text-slate-500" role="status">Loading notifications…</div>}
          {!loading && error && <div className="p-6 text-center"><p className="text-sm text-red-600 dark:text-red-400" role="alert">{error}</p><button type="button" onClick={() => load()} className="mt-2 text-sm font-semibold text-primary-600">Try again</button></div>}
          {!loading && !error && !items.length && <div className="p-8 text-center"><FiBell className="mx-auto mb-2 text-slate-300" size={28} /><p className="font-medium text-slate-700 dark:text-slate-200">You’re all caught up</p><p className="mt-1 text-sm text-slate-500">No notifications yet.</p></div>}
          {!loading && !error && items.map((item) => {
            const Icon = icons[item.type] || FiBell;
            return <div key={item.id} role="menuitem" tabIndex={0} onClick={() => selectItem(item)} onKeyDown={(event) => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); selectItem(item); } }}
              className={`group flex cursor-pointer gap-3 border-b border-slate-100 px-4 py-3 outline-none hover:bg-slate-50 focus:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800 dark:focus:bg-slate-800 ${item.is_read ? "" : "bg-primary-50/60 dark:bg-primary-950/20"}`}>
              <span className="mt-0.5 rounded-full bg-primary-100 p-2 text-primary-600 dark:bg-slate-700 dark:text-primary-300"><Icon size={16} /></span>
              <span className="min-w-0 flex-1"><span className="flex items-start gap-2"><span className={`flex-1 text-sm text-slate-800 dark:text-slate-100 ${item.is_read ? "font-medium" : "font-bold"}`}>{item.title}</span>{!item.is_read && <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary-500" aria-label="Unread" />}</span><span className="mt-0.5 block text-sm text-slate-500 dark:text-slate-400">{item.message}</span><span className="mt-1 block text-xs text-slate-400">{relativeTime(item.created_at)}</span></span>
              <button type="button" onClick={(event) => remove(event, item)} aria-label={`Delete ${item.title}`} className="self-center rounded p-1.5 text-slate-400 opacity-70 hover:bg-red-50 hover:text-red-600 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-400 sm:opacity-0 sm:group-hover:opacity-100"><FiTrash2 /></button>
            </div>;
          })}
        </div>
        <button type="button" onClick={() => { setOpen(false); navigate("/notifications"); }} className="w-full border-t border-slate-100 px-4 py-3 text-sm font-semibold text-primary-600 hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary-500 dark:border-slate-700 dark:text-primary-300 dark:hover:bg-slate-800">View all notifications</button>
      </section>}
    </div>
  );
}
