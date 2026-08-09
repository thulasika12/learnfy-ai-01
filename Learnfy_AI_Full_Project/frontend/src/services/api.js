import axios from "axios";

export const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
});

// Attach JWT token to every request if present
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("learnfy_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

const clearSession = () => {
  localStorage.removeItem("learnfy_token");
  localStorage.removeItem("learnfy_refresh_token");
  localStorage.removeItem("learnfy_user");
};

let refreshRequest = null;

// Retry one failed request after rotating the refresh token.
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const noRefreshPaths = [
      "/auth/login",
      "/auth/register",
      "/auth/refresh",
      "/auth/logout",
      "/auth/forgot-password",
      "/auth/reset-password",
    ];
    const skipRefresh = noRefreshPaths.some((path) => originalRequest?.url?.startsWith(path));
    const refresh = localStorage.getItem("learnfy_refresh_token");

    if (error.response?.status === 401 && !originalRequest?._retry && !skipRefresh && refresh) {
      originalRequest._retry = true;
      try {
        refreshRequest ||= axios
          .post(`${BASE_URL}/auth/refresh`, { refresh_token: refresh })
          .then((res) => {
            localStorage.setItem("learnfy_token", res.data.access_token);
            localStorage.setItem("learnfy_refresh_token", res.data.refresh_token);
            localStorage.setItem("learnfy_user", JSON.stringify(res.data.user));
            return res.data.access_token;
          })
          .finally(() => {
            refreshRequest = null;
          });

        const newToken = await refreshRequest;
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch {
        clearSession();
      }
    } else if (error.response?.status === 401 && !skipRefresh) {
      clearSession();
    }

    if (error.response?.status === 401 && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------
export const registerUser = (data) => api.post("/auth/register", data);
export const loginUser = (data) => api.post("/auth/login", data);
export const forgotPassword = (data) => api.post("/auth/forgot-password", data);
export const resetPassword = (data) => api.post("/auth/reset-password", data);
export const refreshToken = (data) => api.post("/auth/refresh", data);
export const logoutUser = (data) => api.post("/auth/logout", data);
export const changePassword = (data) => api.post("/auth/change-password", data);

// ---------------------------------------------------------------------------
// Payments
// ---------------------------------------------------------------------------
export const getPaymentPlans = () => api.get("/payments/plans");
export const getPaymentConfiguration = () => api.get("/payments/config");
export const createPaymentCheckout = (data) => api.post("/payments/checkout", data);
export const createPayHereOrder = (data) => api.post("/payments/payhere/create-order", data);
export const openBillingPortal = () => api.post("/payments/portal");
export const getMyPayments = () => api.get("/payments/subscription/me");
export const getPaymentStatus = (orderId) => api.get(`/payments/status/${encodeURIComponent(orderId)}`);
export const getAdminTransactions = () => api.get("/payments/admin/transactions");

// ---------------------------------------------------------------------------
// Users
// ---------------------------------------------------------------------------
export const getProfile = () => api.get("/users/profile");
export const getDashboardStats = () => api.get("/dashboard/stats");
export const DASHBOARD_STATS_EVENT = "learnfy:dashboard-stats-changed";
const refreshDashboardStats = () => window.dispatchEvent(new Event(DASHBOARD_STATS_EVENT));
export const updateProfile = (data) => api.put("/users/profile", data);
export const uploadAvatar = (formData) => api.post("/users/profile/avatar", formData);
export const deleteAccount = (data) => api.delete("/users/account", { data });

// ---------------------------------------------------------------------------
// Notes
// ---------------------------------------------------------------------------
export const getNotes = (params) => api.get("/notes/", { params });
export const getNote = (id) => api.get(`/notes/${id}`);
export const uploadNote = (formData) => api.post("/notes/", formData).then((response) => { refreshDashboardStats(); return response; });
export const updateNote = (id, data) => api.put(`/notes/${id}`, data);
export const deleteNote = (id) => api.delete(`/notes/${id}`);
export const toggleLike = (id) => api.post(`/notes/${id}/like`);
export const toggleBookmark = (id) => api.post(`/notes/${id}/bookmark`);

// ---------------------------------------------------------------------------
// Comments
// ---------------------------------------------------------------------------
export const getComments = (noteId) => api.get(`/comments/${noteId}`);
export const postComment = (data) => api.post("/comments/", data);

// ---------------------------------------------------------------------------
// Study Groups
// ---------------------------------------------------------------------------
export const getGroups = () => api.get("/groups/");
export const createGroup = (data) => api.post("/groups/create", data).then((response) => { refreshDashboardStats(); return response; });
export const deleteGroup = (id) => api.delete(`/groups/${id}`);
export const joinGroup = (id) => api.post(`/groups/${id}/join`).then((response) => { if (response.data.status === "approved") refreshDashboardStats(); return response; });
export const leaveGroup = (id) => api.post(`/groups/${id}/leave`).then((response) => { refreshDashboardStats(); return response; });
export const getJoinRequests = (groupId) => api.get(`/groups/${groupId}/join-requests`);
export const approveJoinRequest = (groupId, requestId) =>
  api.post(`/groups/${groupId}/join-requests/${requestId}/approve`);
export const rejectJoinRequest = (groupId, requestId) =>
  api.post(`/groups/${groupId}/join-requests/${requestId}/reject`);
export const getDiscussions = (groupId) => api.get(`/groups/${groupId}/discussions`);
export const postDiscussion = (groupId, data) => api.post(`/groups/${groupId}/discussions`, data);

// ---------------------------------------------------------------------------
// AI
// ---------------------------------------------------------------------------
export const aiChat = (data) => api.post("/ai/chat", data).then((response) => { refreshDashboardStats(); return response; });
export const aiSummarize = (data) => api.post("/ai/summarize", data);
export const aiSummarizeFile = (formData) => api.post("/ai/summarize-file", formData);
export const aiGenerateQuiz = (data) => api.post("/ai/generate-quiz", data);
export const aiSubmitQuiz = (data) => api.post("/ai/quiz/submit", data).then((response) => { refreshDashboardStats(); return response; });
export const aiStudyPlan = (data) => api.post("/ai/study-plan", data);
export const aiFlashcards = (data) => api.post("/ai/flashcards", data);

// ---------------------------------------------------------------------------
// Complete flashcard system
// ---------------------------------------------------------------------------
export const generateFlashcards = (data) => api.post("/flashcards/generate", data);
export const generateFlashcardsFromText = (data) => api.post("/flashcards/generate-from-text", data);
export const generateFlashcardsFromNote = (data) => api.post("/flashcards/generate-from-note", data);
export const generateFlashcardsFromFile = (path, data, onUploadProgress) => api.post(path, data, { onUploadProgress });
export const saveFlashcardSet = (data) => api.post("/flashcards/sets", data);
export const getFlashcardSets = (params) => api.get("/flashcards/sets", { params });
export const getFlashcardSet = (id) => api.get(`/flashcards/sets/${id}`);
export const updateFlashcardSet = (id, data) => api.put(`/flashcards/sets/${id}`, data);
export const deleteFlashcardSet = (id) => api.delete(`/flashcards/sets/${id}`);
export const toggleFlashcardSetFavourite = (id) => api.patch(`/flashcards/sets/${id}/favourite`);
export const toggleFlashcardFavourite = (id) => api.patch(`/flashcards/cards/${id}/favourite`);
export const uploadFlashcardImage = (id, data, onUploadProgress) => api.post(`/flashcards/cards/${id}/image`, data, { onUploadProgress });
export const saveFlashcardStudySession = (id, data) => api.post(`/flashcards/sets/${id}/study-sessions`, data);
export const getFlashcardStudySessions = (id) => api.get(`/flashcards/sets/${id}/study-sessions`);
export const shareFlashcardSet = (id, data) => api.post(`/flashcards/sets/${id}/share`, data);
export const unshareFlashcardSet = (id) => api.delete(`/flashcards/sets/${id}/share`);
export const getSharedFlashcardSet = (token) => api.get(`/flashcards/shared/${encodeURIComponent(token)}`);
export const getFlashcardStats = () => api.get("/flashcards/dashboard/stats");
export const getFlashcardReminder = () => api.get("/flashcards/reminders");
export const updateFlashcardReminder = (data) => api.put("/flashcards/reminders", data);
export const flashcardExportUrl = (id, format) => `${BASE_URL}/flashcards/sets/${id}/export/${format}`;
export const getChatHistory = (params) => api.get("/chat/history", { params });

// Notifications (JWT is supplied by the shared request interceptor)
export const getNotifications = (params) => api.get("/notifications", { params });
export const getUnreadNotificationCount = () => api.get("/notifications/unread-count");
export const markNotificationRead = (id) => api.patch(`/notifications/${id}/read`);
export const markAllNotificationsRead = () => api.patch("/notifications/read-all");
export const deleteNotification = (id) => api.delete(`/notifications/${id}`);

// ---------------------------------------------------------------------------
// Teacher resources
// ---------------------------------------------------------------------------
export const getResources = (params) => api.get("/resources/", { params });
export const uploadResource = (formData) => api.post("/resources/", formData);
export const deleteResource = (id) => api.delete(`/resources/${id}`);

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------
export const getAllUsers = (params) => api.get("/admin/users", { params });
export const getUsersPage = (params) => api.get("/admin/users/page", { params });
export const deactivateUser = (id, reason) => api.put(`/admin/users/${id}/deactivate`, { reason });
export const restoreUser = (id, reason) => api.put(`/admin/users/${id}/restore`, { reason });
export const permanentlyDeleteUser = (id, reason) => api.delete(`/admin/users/${id}`, { data: { reason } });
export const getSubjects = (params) => api.get("/subjects", { params });
export const getEducationLevels = () => api.get("/academic/levels");
export const getGrades = (params) => api.get("/academic/grades", { params });
export const getAcademicStreams = () => api.get("/academic/streams");
export const getAcademicProfile = () => api.get("/academic/profile");
export const updateAcademicProfile = (data) => api.put("/academic/profile", data);
export const submitTeacherVerification = (data) => api.post("/teacher-verifications", data);
export const getMyTeacherVerification = () => api.get("/teacher-verifications/me");
export const getMyTeacherVerificationDocument = (id) => api.get(`/teacher-verifications/${id}/document`, { responseType: "blob" });
export const getTeacherVerifications = (status) => api.get("/admin/teacher-verifications", { params: { status: status || undefined } });
export const approveTeacherVerification = (id) => api.post(`/admin/teacher-verifications/${id}/approve`);
export const rejectTeacherVerification = (id, reason) => api.post(`/admin/teacher-verifications/${id}/reject`, { reason });
export const getTeacherVerificationDocument = (id) => api.get(`/admin/teacher-verifications/${id}/document`, { responseType: "blob" });
export const getSubject = (id) => api.get(`/subjects/${id}`);
export const getAdminSubjects = (params) => api.get("/admin/subjects", { params });
export const createSubject = (data) => api.post("/admin/subjects", data);
export const updateSubject = (id, data) => api.put(`/admin/subjects/${id}`, data);
export const deleteSubject = (id) => api.delete(`/admin/subjects/${id}`);
export const getReportedNotes = () => api.get("/admin/notes/reported");
export const getStatistics = () => api.get("/admin/statistics");
export const getModerationReports = (params) => api.get("/admin/moderation/reports", { params });
export const moderateReport = (id, action, note) => api.post(`/admin/moderation/reports/${id}/action`, { action, note });
export const getAdminPayments = () => api.get("/payments/admin/transactions");
export const getAuditLogs = (params) => api.get("/admin/audit-logs", { params });
export const getMyStudentVerification = () => api.get("/student-verifications/me");
export const submitStudentVerification = (data) => api.post("/student-verifications", data);
export const getStudentVerifications = (status) => api.get("/admin/student-verifications", { params: { status: status || undefined } });
export const approveStudentVerification = (id) => api.post(`/admin/student-verifications/${id}/approve`);
export const rejectStudentVerification = (id, reason) => api.post(`/admin/student-verifications/${id}/reject`, { reason });
export const getStudentVerificationDocument = (id) => api.get(`/admin/student-verifications/${id}/document`, { responseType: "blob" });

export default api;
