import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { useLocation } from "react-router-dom";

export const easeOut = [0.22, 1, 0.36, 1];

export function PageTransition({ children, className = "" }) {
  const location = useLocation(); const reduce = useReducedMotion();
  return <AnimatePresence mode="wait" initial={false}><motion.div key={location.pathname} className={className} initial={reduce ? { opacity: 1 } : { opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={reduce ? { opacity: 1 } : { opacity: 0, y: -4 }} transition={{ duration: reduce ? 0 : 0.22, ease: easeOut }}>{children}</motion.div></AnimatePresence>;
}

export function Reveal({ children, className = "", delay = 0, direction = "up", once = true }) {
  const reduce = useReducedMotion(); const offset = direction === "left" ? { x: 18 } : direction === "right" ? { x: -18 } : { y: 18 };
  return <motion.div className={className} initial={reduce ? false : { opacity: 0, ...offset }} whileInView={{ opacity: 1, x: 0, y: 0 }} viewport={{ once, amount: 0.15 }} transition={{ duration: reduce ? 0 : 0.45, delay: reduce ? 0 : delay, ease: easeOut }}>{children}</motion.div>;
}

export function CountUp({ value, duration = 700 }) {
  const reduce = useReducedMotion(); const [shown, setShown] = useState(0); const previous = useRef(0);
  useEffect(() => { const target = Number(value); if (!Number.isFinite(target)) return; if (reduce) { setShown(target); previous.current = target; return; } const from = previous.current; const start = performance.now(); let frame; const tick = now => { const progress = Math.min((now - start) / duration, 1); setShown(Math.round(from + (target - from) * (1 - Math.pow(1 - progress, 3)))); if (progress < 1) frame = requestAnimationFrame(tick); else previous.current = target; }; frame = requestAnimationFrame(tick); return () => cancelAnimationFrame(frame); }, [duration, reduce, value]);
  return shown;
}

export function SkeletonGrid({ count = 6 }) {
  return <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3" aria-label="Loading content" role="status">{Array.from({ length: count }, (_, index) => <div key={index} className="glass-card animate-pulse p-5 motion-reduce:animate-none"><div className="h-5 w-24 rounded-full bg-slate-200 dark:bg-slate-700"/><div className="mt-5 h-5 w-4/5 rounded bg-slate-200 dark:bg-slate-700"/><div className="mt-3 h-3 w-full rounded bg-slate-100 dark:bg-slate-800"/><div className="mt-2 h-3 w-2/3 rounded bg-slate-100 dark:bg-slate-800"/></div>)}<span className="sr-only">Loading…</span></div>;
}

export function TypingIndicator({ label = "AI is thinking" }) {
  return <div role="status" className="flex items-center gap-2 pl-11 text-sm text-slate-500"><span className="sr-only">{label}</span>{[0,1,2].map(item => <motion.span key={item} className="h-2 w-2 rounded-full bg-primary-500" animate={{ opacity: [0.35, 1, 0.35], y: [0, -3, 0] }} transition={{ duration: 0.9, repeat: Infinity, delay: item * 0.14 }}/>)}</div>;
}
