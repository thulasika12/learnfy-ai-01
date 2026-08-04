import { NavLink } from "react-router-dom";
import {
  FiHome,
  FiFileText,
  FiUpload,
  FiMessageCircle,
  FiFileText as FiSummary,
  FiHelpCircle,
  FiUsers,
  FiUser,
  FiSettings,
  FiShield,
  FiCalendar,
  FiLayers,
  FiCreditCard,
  FiCheckSquare,
  FiActivity,
  FiBookOpen,
  FiFlag,
} from "react-icons/fi";
import { useAuth } from "../hooks/useAuth";
import { usePreferences } from "../hooks/usePreferences";

const studentLinks = [
  { to: "/dashboard", labelKey: "sidebar.dashboard", icon: FiHome },
  { to: "/notes", labelKey: "sidebar.notes", icon: FiFileText },
  { to: "/resources", labelKey: "sidebar.resources", icon: FiFileText },
  { to: "/notes/upload", labelKey: "sidebar.uploadNote", icon: FiUpload },
  { to: "/ai/chat", labelKey: "sidebar.aiDoubtSolver", icon: FiMessageCircle },
  { to: "/ai/summary", labelKey: "sidebar.aiSummarizer", icon: FiSummary },
  { to: "/ai/quiz", labelKey: "sidebar.quizGenerator", icon: FiHelpCircle },
  { to: "/ai/planner", labelKey: "sidebar.studyPlanner", icon: FiCalendar },
  { to: "/ai/flashcards", labelKey: "sidebar.flashcards", icon: FiLayers },
  { to: "/groups", labelKey: "sidebar.studyGroups", icon: FiUsers },
  { to: "/teacher-verification", labelKey: "sidebar.applyTeacher", icon: FiShield },
  { to: "/student-verification", labelKey: "sidebar.studentVerification", icon: FiCheckSquare },
];

const teacherLinks = [
  { to: "/teacher/dashboard", labelKey: "sidebar.dashboard", icon: FiHome },
  { to: "/notes", labelKey: "sidebar.notesResources", icon: FiFileText },
  { to: "/resources", labelKey: "sidebar.teacherResources", icon: FiFileText },
  { to: "/notes/upload", labelKey: "sidebar.uploadMaterial", icon: FiUpload },
  { to: "/ai/chat", labelKey: "sidebar.aiAssistant", icon: FiMessageCircle },
  { to: "/groups", labelKey: "sidebar.studyGroups", icon: FiUsers },
];

const adminLinks = [
  { to: "/admin/dashboard", labelKey: "sidebar.adminDashboard", icon: FiShield },
  { to: "/admin/users", labelKey: "sidebar.adminUsers", icon: FiUsers },
  { to: "/admin/teacher-verifications", labelKey: "sidebar.teacherVerifications", icon: FiCheckSquare },
  { to: "/admin/student-verifications", labelKey: "sidebar.studentVerifications", icon: FiCheckSquare },
  { to: "/admin/subjects", labelKey: "sidebar.adminSubjects", icon: FiBookOpen },
  { to: "/admin/moderation", labelKey: "sidebar.adminModeration", icon: FiFlag },
  { to: "/admin/payments", labelKey: "sidebar.adminPayments", icon: FiCreditCard },
  { to: "/admin/audit-logs", labelKey: "sidebar.adminAuditLogs", icon: FiActivity },
];

const commonLinks = [
  { to: "/payments", labelKey: "sidebar.payments", icon: FiCreditCard },
  { to: "/profile", labelKey: "sidebar.profile", icon: FiUser },
  { to: "/settings", labelKey: "sidebar.settings", icon: FiSettings },
];

function NavItems({ links, onClose, t, admin = false }) {
  return <>
    {links.map((link) => <NavLink key={link.to} to={link.to} onClick={onClose} className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link-active" : ""}`}><link.icon size={18} />{t(link.labelKey)}</NavLink>)}
    <div className="border-t border-slate-100 my-3" />
    {commonLinks.filter(link=>!admin||link.to!=="/payments").map((link) => <NavLink key={link.to} to={link.to} onClick={onClose} className={({ isActive }) => `sidebar-link ${isActive ? "sidebar-link-active" : ""}`}><link.icon size={18} />{t(link.labelKey)}</NavLink>)}
  </>;
}

export default function Sidebar({ mobileOpen, onClose }) {
  const { user } = useAuth();
  const { t } = usePreferences();

  let links = studentLinks;
  if (user?.role === "teacher" && user?.is_verified_teacher) links = teacherLinks;
  if (user?.role === "teacher" && !user?.is_verified_teacher) links = [{ to: "/teacher-verification", labelKey: "sidebar.teacherVerification", icon: FiCheckSquare }, ...studentLinks];
  if (user?.role === "admin") links = adminLinks;

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:flex-col w-64 shrink-0 h-[calc(100vh-4rem)] sticky top-16 border-r border-slate-100 dark:border-slate-700 bg-white/60 dark:bg-slate-900/80 backdrop-blur-md p-4 gap-1 overflow-y-auto">
        <NavItems links={links} onClose={onClose} t={t} admin={user?.role==="admin"} />
      </aside>

      {/* Mobile sidebar overlay */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={onClose} />
          <aside className="absolute left-0 top-0 h-full w-64 bg-white dark:bg-slate-900 p-4 flex flex-col gap-1 shadow-xl">
            <div className="flex items-center gap-2 mb-4 px-2">
              <img src="/images/logo.png" alt="Learnfy AI" className="w-8 h-8 rounded-lg" />
              <span className="font-bold text-slate-800">Learnfy AI</span>
            </div>
            <NavItems links={links} onClose={onClose} t={t} admin={user?.role==="admin"} />
          </aside>
        </div>
      )}
    </>
  );
}
