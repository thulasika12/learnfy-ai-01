import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";

import MainLayout from "../layouts/MainLayout";
import AuthLayout from "../layouts/AuthLayout";
import DashboardLayout from "../layouts/DashboardLayout";
import ProtectedRoute from "../components/ProtectedRoute";

import Home from "../pages/Home";
import Login from "../pages/Auth/Login";
import Register from "../pages/Auth/Register";
import ForgotPassword from "../pages/Auth/ForgotPassword";
import ResetPassword from "../pages/Auth/ResetPassword";

import NotesList from "../pages/Notes/NotesList";
import NoteDetails from "../pages/Notes/NoteDetails";
import CreateNote from "../pages/Notes/CreateNote";
import EditNote from "../pages/Notes/EditNote";

import Dashboard from "../pages/Student/Dashboard";
import Profile from "../pages/Student/Profile";
import ProgressPage from "../pages/Student/Progress";
import Settings from "../pages/Student/Settings";
import Notifications from "../pages/Student/Notifications";

const TeacherDashboard = lazy(() => import("../pages/Teacher/Dashboard"));
const TeacherVerification = lazy(() => import("../pages/Teacher/Verification"));
const AdminDashboard = lazy(() => import("../pages/Admin/AdminDashboard"));
const SubjectManagement = lazy(() => import("../pages/Admin/SubjectManagement"));
const TeacherVerifications = lazy(() => import("../pages/Admin/TeacherVerifications"));
import StudentVerification from "../pages/Student/StudentVerification";
const StudentVerifications = lazy(() => import("../pages/Admin/StudentVerifications"));
const UserManagement = lazy(() => import("../pages/Admin/UserManagement"));
const ContentModeration = lazy(() => import("../pages/Admin/ContentModeration"));
const PaymentAdministration = lazy(() => import("../pages/Admin/PaymentAdministration"));
const AuditLogs = lazy(() => import("../pages/Admin/AuditLogs"));

const AIChat = lazy(() => import("../pages/AI/AIChat"));
const PDFSummary = lazy(() => import("../pages/AI/PDFSummary"));
const QuizGenerator = lazy(() => import("../pages/AI/QuizGenerator"));
const StudyPlanner = lazy(() => import("../pages/AI/StudyPlanner"));
const Flashcards = lazy(() => import("../pages/AI/Flashcards"));
const FlashcardDetails = lazy(() => import("../pages/AI/FlashcardDetails"));
const SharedFlashcard = lazy(() => import("../pages/AI/SharedFlashcard"));

import StudyGroups from "../pages/Community/StudyGroups";
import Resources from "../pages/Resources/Resources";
const Pricing = lazy(() => import("../pages/Payments/Pricing"));
const PaymentCheckout = lazy(() => import("../pages/Payments/Checkout"));
const PaymentResult = lazy(() => import("../pages/Payments/PaymentResult"));
const Subscription = lazy(() => import("../pages/Payments/Subscription"));
const TrustPage = lazy(() => import("../pages/TrustPage"));

function RouteLoading() {
  return <div role="status" className="flex min-h-64 items-center justify-center text-sm font-semibold text-primary-600">Loading Learnfy AI…</div>;
}

export default function AppRoutes() {
  return (
    <Suspense fallback={<RouteLoading />}><Routes>
      {/* Public pages with navbar + footer */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/notes" element={<NotesList />} />
        <Route path="/notes/:id" element={<NoteDetails />} />
        <Route path="/resources" element={<Resources />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/flashcards/shared/:token" element={<SharedFlashcard />} />
        <Route path="/about" element={<TrustPage page="about" />} />
        <Route path="/support" element={<TrustPage page="support" />} />
        <Route path="/faq" element={<TrustPage page="faq" />} />
        <Route path="/privacy" element={<TrustPage page="privacy" />} />
        <Route path="/terms" element={<TrustPage page="terms" />} />
        <Route path="/refunds" element={<TrustPage page="refunds" />} />
        <Route path="/community-guidelines" element={<TrustPage page="community" />} />
        <Route path="/ai-disclaimer" element={<TrustPage page="ai" />} />
        <Route path="/data-deletion" element={<TrustPage page="deletion" />} />
      </Route>

      {/* Auth pages (split-screen branding layout) */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
      </Route>

      {/* Authenticated app (sidebar + navbar) */}
      <Route
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/payments" element={<Subscription />} />
        <Route path="/payments/checkout" element={<PaymentCheckout />} />
        <Route path="/payments/result" element={<PaymentResult />} />

        <Route path="/notes/upload" element={<CreateNote />} />
        <Route path="/notes/:id/edit" element={<EditNote />} />

        <Route path="/ai/chat" element={<AIChat />} />
        <Route path="/ai/summary" element={<PDFSummary />} />
        <Route path="/ai/quiz" element={<QuizGenerator />} />
        <Route path="/ai/planner" element={<StudyPlanner />} />
        <Route path="/ai/flashcards" element={<Flashcards />} />
        <Route path="/flashcards/:id" element={<FlashcardDetails />} />

        <Route path="/groups" element={<StudyGroups />} />
        <Route path="/teacher-verification" element={<TeacherVerification />} />
        <Route path="/student-verification" element={<StudentVerification />} />

        <Route
          path="/teacher/dashboard"
          element={
            <ProtectedRoute allowedRoles={["teacher", "admin"]}>
              <TeacherDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/dashboard"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route path="/admin/subjects" element={<ProtectedRoute allowedRoles={["admin"]}><SubjectManagement /></ProtectedRoute>} />
        <Route path="/admin/teacher-verifications" element={<ProtectedRoute allowedRoles={["admin"]}><TeacherVerifications /></ProtectedRoute>} />
        <Route path="/admin/student-verifications" element={<ProtectedRoute allowedRoles={["admin"]}><StudentVerifications /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["admin"]}><UserManagement /></ProtectedRoute>} />
        <Route path="/admin/moderation" element={<ProtectedRoute allowedRoles={["admin"]}><ContentModeration /></ProtectedRoute>} />
        <Route path="/admin/payments" element={<ProtectedRoute allowedRoles={["admin"]}><PaymentAdministration /></ProtectedRoute>} />
        <Route path="/admin/audit-logs" element={<ProtectedRoute allowedRoles={["admin"]}><AuditLogs /></ProtectedRoute>} />
      </Route>

      <Route path="*" element={<Home />} />
    </Routes></Suspense>
  );
}
