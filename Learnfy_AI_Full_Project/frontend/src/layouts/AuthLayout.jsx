import { Link, Outlet } from "react-router-dom";
import { motion } from "framer-motion";
import { FiMoon, FiSun } from "react-icons/fi";
import { usePreferences } from "../hooks/usePreferences";

export default function AuthLayout() {
  const { theme, toggleTheme, language, setLanguage, t } = usePreferences();
  return <div className="grid min-h-screen bg-[#030712] font-sans md:grid-cols-2">
    <div className="relative hidden overflow-hidden bg-[linear-gradient(135deg,#111827_0%,#1F2937_50%,#374151_100%)] p-10 text-white md:flex md:flex-col md:justify-between lg:p-14 xl:p-16">
      <div className="pointer-events-none absolute inset-0 opacity-[0.12] [background-image:radial-gradient(rgba(255,255,255,0.8)_1px,transparent_1px)] [background-size:24px_24px]" />
      <motion.div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-gradient-to-br from-sky-200/30 via-blue-300/15 to-transparent blur-3xl" animate={{ scale: [1, 1.08, 1], x: [0, -12, 0], y: [0, 10, 0] }} transition={{ repeat: Infinity, duration: 9, ease: "easeInOut" }} />
      <motion.div className="pointer-events-none absolute -bottom-28 -left-24 h-96 w-96 rounded-full bg-gradient-to-tr from-black/80 via-blue-500/20 to-transparent blur-3xl" animate={{ scale: [1, 1.1, 1], x: [0, 16, 0] }} transition={{ repeat: Infinity, duration: 11, ease: "easeInOut" }} />
      <div className="pointer-events-none absolute left-[28%] top-[38%] h-52 w-52 rounded-full bg-sky-300/15 blur-[80px]" />
      <Link to="/" className="z-10 flex w-fit items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/[0.05] px-3.5 py-2.5 backdrop-blur-[18px] transition duration-300 hover:bg-white/10">
        <img src="/images/logo.png" alt="Learnfy AI" className="h-10 w-10 rounded-xl object-cover shadow-lg shadow-black/30" />
        <span className="text-xl font-extrabold tracking-tight">Learnfy AI</span>
      </Link>
      <div className="z-10 max-w-xl py-14">
        <div className="mb-7 inline-flex items-center rounded-full border border-blue-300/15 bg-blue-400/[0.06] px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-[#60A5FA] backdrop-blur-[18px]">Your intelligent learning companion</div>
        <h1 className="mb-6 text-4xl font-extrabold leading-[1.12] tracking-tight lg:text-5xl xl:text-[3.4rem]">Learn Smarter with<br />AI-Powered Study Support</h1>
        <p className="max-w-lg text-base leading-8 text-slate-200 lg:text-lg">Share notes, resolve doubts instantly, generate quizzes, and build a personalized study plan — all powered by AI.</p>
      </div>
      <div className="z-10 flex items-center gap-3 text-sm font-medium text-slate-300"><span>Learn</span><span className="h-1 w-1 rounded-full bg-[#60A5FA]"/><span>Connect</span><span className="h-1 w-1 rounded-full bg-[#60A5FA]"/><span>Grow</span></div>
    </div>

    <div className="relative flex min-h-screen items-center justify-center overflow-x-hidden bg-[#030712] px-5 py-24 sm:px-8 md:min-h-0 md:p-12 lg:p-16">
      <div className="pointer-events-none absolute inset-0 opacity-[0.035] [background-image:linear-gradient(rgba(148,163,184,0.5)_1px,transparent_1px),linear-gradient(90deg,rgba(148,163,184,0.5)_1px,transparent_1px)] [background-size:40px_40px]" />
      <div className="pointer-events-none absolute right-[-8rem] top-[20%] h-72 w-72 rounded-full bg-blue-400/10 blur-[100px]" />
      <div className="absolute right-4 top-4 z-20 flex items-center gap-2 sm:right-6 sm:top-6">
        <button type="button" onClick={toggleTheme} title={theme === "dark" ? t("theme.switchToLight") : t("theme.switchToDark")} className="rounded-xl border border-white/[0.08] bg-white/[0.05] p-2.5 text-slate-300 backdrop-blur-[18px] transition duration-300 hover:scale-105 hover:border-blue-400/40 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400">{theme === "dark" ? <FiSun /> : <FiMoon />}</button>
        <select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label={t("settings.language")} className="rounded-xl border border-white/[0.08] bg-[#111827] px-3 py-2.5 text-sm text-slate-200 outline-none transition duration-300 hover:border-blue-400/40 focus:border-blue-400 focus:ring-2 focus:ring-blue-500/25"><option value="en">EN</option><option value="ta">தமிழ்</option><option value="si">සිංහල</option></select>
      </div>
      <div className="relative z-10 w-full max-w-[29rem]">
        <div className="mb-10 flex items-center justify-center gap-3 md:hidden"><img src="/images/logo.png" alt="Learnfy AI" className="h-10 w-10 rounded-xl" /><span className="text-xl font-extrabold tracking-tight text-slate-50">Learnfy AI</span></div>
        <Outlet />
      </div>
    </div>
  </div>;
}
