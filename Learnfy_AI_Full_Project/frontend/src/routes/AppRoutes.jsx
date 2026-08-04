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

import TeacherDashboard from "../pages/Teacher/Dashboard";
import TeacherVerification from "../pages/Teacher/Verification";
import AdminDashboard from "../pages/Admin/AdminDashboard";
import SubjectManagement from "../pages/Admin/SubjectManagement";
import TeacherVerifications from "../pages/Admin/TeacherVerifications";
import StudentVerification from "../pages/Student/StudentVerification";
import StudentVerifications from "../pages/Admin/StudentVerifications";
import UserManagement from "../pages/Admin/UserManagement";
import ContentModeration from "../pages/Admin/ContentModeration";
import PaymentAdministration from "../pages/Admin/PaymentAdministration";
import AuditLogs from "../pages/Admin/AuditLogs";

import AIChat from "../pages/AI/AIChat";
import PDFSummary from "../pages/AI/PDFSummary";
import QuizGenerator from "../pages/AI/QuizGenerator";
import StudyPlanner from "../pages/AI/StudyPlanner";
import Flashcards from "../pages/AI/Flashcards";
import FlashcardDetails from "../pages/AI/FlashcardDetails";
import SharedFlashcard from "../pages/AI/SharedFlashcard";

import StudyGroups from "../pages/Community/StudyGroups";
import Resources from "../pages/Resources/Resources";
import Pricing from "../pages/Payments/Pricing";
import PaymentCheckout from "../pages/Payments/Checkout";
import PaymentResult from "../pages/Payments/PaymentResult";
import Subscription from "../pages/Payments/Subscription";

export default function AppRoutes() {
  return (
    <Routes>
      {/* Public pages with navbar + footer */}
      <Route element={<MainLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/notes" element={<NotesList />} />
        <Route path="/notes/:id" element={<NoteDetails />} />
        <Route path="/resources" element={<Resources />} />
        <Route path="/pricing" element={<Pricing />} />
        <Route path="/flashcards/shared/:token" element={<SharedFlashcard />} />
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
    </Routes>
  );
}
