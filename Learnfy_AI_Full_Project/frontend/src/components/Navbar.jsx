import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import { FiChevronDown, FiGlobe, FiLogOut, FiMenu, FiMoon, FiSettings, FiSun, FiUser, FiX } from "react-icons/fi";

import { useAuth } from "../hooks/useAuth";
import { usePreferences } from "../hooks/usePreferences";
import NotificationMenu from "./NotificationMenu";

const primaryLinks = [
  ["/", "nav.home"], ["/notes", "nav.exploreNotes"], ["/resources", "nav.resources"],
  ["/groups", "nav.studyGroups"], ["/pricing", "nav.pricing"], ["/dashboard", "nav.dashboard"],
];
const aiLinks = [
  ["/ai/chat", "nav.aiDoubtSolver"], ["/ai/summary", "nav.aiSummarizer"],
  ["/ai/quiz", "nav.quizGenerator"], ["/ai/flashcards", "nav.flashcards"], ["/ai/planner", "nav.studyPlanner"],
];
const linkClass = ({ isActive }) => `rounded-lg px-2.5 py-2 text-sm font-medium transition-colors ${isActive ? "bg-primary-50 text-primary-700 dark:bg-slate-800 dark:text-primary-300" : "text-slate-600 hover:text-primary-600 dark:text-slate-300"}`;

function NavigationLinks({ mobile=false, links, t, aiOpen, setAiOpen, aiRef }) {
  return <div className={mobile?"grid gap-1":"hidden items-center gap-0.5 xl:flex"}>
    {links.slice(0,3).map(([to,key])=><NavLink key={to} end={to==="/"} to={to} className={linkClass}>{t(key)}</NavLink>)}
    <div ref={mobile?undefined:aiRef} className="relative">
      <button type="button" aria-expanded={aiOpen} aria-haspopup="menu" onClick={()=>setAiOpen(open=>!open)} className="flex w-full items-center gap-1 rounded-lg px-2.5 py-2 text-sm font-medium text-slate-600 hover:text-primary-600 dark:text-slate-300">{t("nav.aiTools")}<FiChevronDown/></button>
      {aiOpen&&<div role="menu" className={`${mobile?"ml-3":"absolute left-0 top-full z-50 mt-1 w-56 shadow-xl"} rounded-xl border border-slate-200 bg-white p-2 dark:border-slate-700 dark:bg-slate-900`}>{aiLinks.map(([to,key])=><NavLink key={to} to={to} className={({isActive})=>`block rounded-lg px-3 py-2 text-sm ${isActive?"bg-primary-50 text-primary-700 dark:bg-slate-800":"hover:bg-slate-50 dark:hover:bg-slate-800"}`}>{t(key)}</NavLink>)}</div>}
    </div>
    {links.slice(3).map(([to,key])=><NavLink key={to} to={to} className={linkClass}>{t(key)}</NavLink>)}
  </div>;
}

export default function Navbar({ onToggleSidebar, showSidebarToggle = false }) {
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme, language, setLanguage, t } = usePreferences();
  const [profileOpen, setProfileOpen] = useState(false); const [aiOpen, setAiOpen] = useState(false); const [mobileOpen, setMobileOpen] = useState(false);
  const profileRef = useRef(null); const aiRef = useRef(null); const location = useLocation(); const navigate = useNavigate();
  useEffect(()=>{setMobileOpen(false);setAiOpen(false);setProfileOpen(false);},[location.pathname]);
  useEffect(()=>{const close=(event)=>{if(!profileRef.current?.contains(event.target))setProfileOpen(false);if(!aiRef.current?.contains(event.target))setAiOpen(false);};const escape=(event)=>{if(event.key==="Escape"){setMobileOpen(false);setAiOpen(false);setProfileOpen(false);}};document.addEventListener("pointerdown",close);document.addEventListener("keydown",escape);return()=>{document.removeEventListener("pointerdown",close);document.removeEventListener("keydown",escape);};},[]);
  const handleLogout=async()=>{await logout();navigate("/login");};
  const visibleLinks=user?.role==="admin"?[...primaryLinks,["/admin/dashboard","nav.admin"]]:primaryLinks;

  return <header className="sticky top-0 z-40 border-b border-slate-100 bg-white/90 backdrop-blur-md dark:border-slate-700 dark:bg-slate-900/95">
    <div className="mx-auto flex min-h-16 max-w-[90rem] items-center justify-between gap-3 px-4 md:px-6">
      <div className="flex min-w-0 items-center gap-2">{showSidebarToggle&&<button type="button" onClick={onToggleSidebar} aria-label="Open sidebar" className="rounded-lg p-2 md:hidden"><FiMenu size={22}/></button>}<Link to="/" className="flex shrink-0 items-center gap-2"><img src="/images/logo.png" alt="Learnfy AI" className="h-9 w-9 rounded-lg object-cover"/><span className="hidden font-extrabold tracking-tight sm:inline">Learnfy AI</span></Link></div>
      <NavigationLinks links={visibleLinks} t={t} aiOpen={aiOpen} setAiOpen={setAiOpen} aiRef={aiRef}/>
      <div className="flex shrink-0 items-center gap-1.5">
        <button type="button" onClick={toggleTheme} aria-label={theme==="dark"?t("theme.switchToLight"):t("theme.switchToDark")} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800">{theme==="dark"?<FiSun/>:<FiMoon/>}</button>
        <label className="relative hidden items-center sm:flex"><FiGlobe className="pointer-events-none absolute left-2.5 text-slate-400"/><select value={language} onChange={e=>setLanguage(e.target.value)} aria-label={t("settings.language")} className="rounded-lg border border-slate-200 bg-white py-2 pl-8 pr-2 text-sm dark:border-slate-600 dark:bg-slate-800"><option value="en">EN</option><option value="ta">தமிழ்</option><option value="si">සිංහල</option></select></label>
        {isAuthenticated?<><NotificationMenu/><div ref={profileRef} className="relative"><button type="button" onClick={()=>setProfileOpen(open=>!open)} aria-expanded={profileOpen} aria-haspopup="menu" className="flex items-center gap-1 rounded-xl p-1.5 hover:bg-slate-100 dark:hover:bg-slate-800"><img src={user?.profile_image||`https://api.dicebear.com/7.x/initials/svg?seed=${user?.name}`} alt="" className="h-8 w-8 rounded-full"/><FiChevronDown/></button>{profileOpen&&<div role="menu" className="absolute right-0 top-full z-50 mt-2 w-48 rounded-xl border border-slate-200 bg-white p-2 shadow-xl dark:border-slate-700 dark:bg-slate-900"><NavLink to="/profile" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800"><FiUser/>{t("nav.profile")}</NavLink><NavLink to="/settings" className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800"><FiSettings/>{t("nav.settings")}</NavLink><button type="button" onClick={handleLogout} className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"><FiLogOut/>{t("nav.logout")}</button></div>}</div></>:<div className="hidden items-center gap-2 md:flex"><NavLink to="/login" className={linkClass}>{t("nav.login")}</NavLink><Link to="/register" className="btn-primary px-3 py-2">{t("nav.getStarted")}</Link></div>}
        <button type="button" onClick={()=>setMobileOpen(open=>!open)} aria-expanded={mobileOpen} aria-label={mobileOpen?"Close navigation":"Open navigation"} className="rounded-lg p-2 xl:hidden">{mobileOpen?<FiX size={21}/>:<FiMenu size={21}/>}</button>
      </div>
    </div>
    {mobileOpen&&<nav aria-label="Main navigation" className="border-t border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900 xl:hidden"><NavigationLinks mobile links={visibleLinks} t={t} aiOpen={aiOpen} setAiOpen={setAiOpen} aiRef={aiRef}/>{!isAuthenticated&&<div className="mt-3 grid grid-cols-2 gap-2 border-t border-slate-200 pt-3 dark:border-slate-700"><NavLink to="/login" className={linkClass}>{t("nav.login")}</NavLink><Link to="/register" className="btn-primary py-2">{t("nav.getStarted")}</Link></div>}</nav>}
  </header>;
}
