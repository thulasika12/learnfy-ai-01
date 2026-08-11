import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import Loader from "./Loader";

export default function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, loading, user } = useAuth();
  const location = useLocation();

  if (loading) return <Loader full label="Checking your session..." />;

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  const onboardingRoute = location.pathname === "/onboarding";
  const emailVerificationRoute = location.pathname === "/verify-email";
  if (user?.role !== "admin" && !user?.is_email_verified && !emailVerificationRoute) {
    return <Navigate to="/verify-email" replace />;
  }
  if (user?.is_email_verified && emailVerificationRoute) {
    return <Navigate to={user?.onboarding_completed ? (user.role === "teacher" ? "/teacher-verification" : "/dashboard") : "/onboarding"} replace />;
  }
  if (user?.role !== "admin" && !user?.onboarding_completed && !onboardingRoute && !emailVerificationRoute) {
    return <Navigate to="/onboarding" replace />;
  }
  if ((user?.role === "admin" || user?.onboarding_completed) && onboardingRoute) {
    const destination = user?.role === "admin" ? "/admin/dashboard" : user?.role === "teacher" ? "/teacher-verification" : "/dashboard";
    return <Navigate to={destination} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  if (allowedRoles?.includes("teacher") && user?.role === "teacher" && !user?.is_verified_teacher) {
    return <Navigate to="/teacher-verification" replace />;
  }

  return children;
}
