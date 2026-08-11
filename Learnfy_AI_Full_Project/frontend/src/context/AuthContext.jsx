import { createContext, useState, useEffect, useCallback } from "react";
import { loginUser, registerUser, getProfile, logoutUser, completeOnboarding, verifyEmail } from "../services/api";

export const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("learnfy_token");
    const cachedUser = localStorage.getItem("learnfy_user");

    if (token && cachedUser) {
      try {
        setUser(JSON.parse(cachedUser));
      } catch {
        localStorage.removeItem("learnfy_user");
      }
      // Refresh profile in background to make sure it's still valid
      getProfile()
        .then((res) => {
          setUser(res.data);
          localStorage.setItem("learnfy_user", JSON.stringify(res.data));
        })
        .catch(() => {
          setUser(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = async (email, password) => {
    const res = await loginUser({ email, password });
    localStorage.setItem("learnfy_token", res.data.access_token);
    localStorage.setItem("learnfy_refresh_token", res.data.refresh_token);
    localStorage.setItem("learnfy_user", JSON.stringify(res.data.user));
    setUser(res.data.user);
    return res.data.user;
  };

  const register = async (name, email, password, confirmPassword) => {
    const res = await registerUser({ name, email, password, confirm_password: confirmPassword });
    return res.data;
  };

  const logout = async (revokeServerToken = true) => {
    const refreshToken = localStorage.getItem("learnfy_refresh_token");
    try {
      if (revokeServerToken && refreshToken) {
        await logoutUser({ refresh_token: refreshToken });
      }
    } catch {
      // Local logout must still complete if the token is already invalid.
    } finally {
      localStorage.removeItem("learnfy_token");
      localStorage.removeItem("learnfy_user");
      localStorage.removeItem("learnfy_refresh_token");
      setUser(null);
    }
  };

  const updateUserCache = useCallback((updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("learnfy_user", JSON.stringify(updatedUser));
  }, []);

  const refreshUser = useCallback(async () => {
    const res = await getProfile();
    updateUserCache(res.data);
    return res.data;
  }, [updateUserCache]);

  const finishOnboarding = useCallback(async (payload) => {
    const res = await completeOnboarding(payload);
    localStorage.setItem("learnfy_token", res.data.access_token);
    localStorage.setItem("learnfy_refresh_token", res.data.refresh_token);
    updateUserCache(res.data.user);
    return res.data.user;
  }, [updateUserCache]);

  const confirmEmail = useCallback(async (code) => {
    const res = await verifyEmail({ code });
    localStorage.setItem("learnfy_token", res.data.access_token); localStorage.setItem("learnfy_refresh_token", res.data.refresh_token); updateUserCache(res.data.user);
    return res.data.user;
  }, [updateUserCache]);

  return (
    <AuthContext.Provider
      value={{ user, loading, login, register, logout, updateUserCache, refreshUser, finishOnboarding, confirmEmail, isAuthenticated: !!user }}
    >
      {children}
    </AuthContext.Provider>
  );
}
