import { createContext, useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  sendRegisterOtp,
  verifyRegisterOtp,
  sendLoginOtp,
  verifyLoginOtp,
  resendOtp,
  getProfile,
  changePassword as apiChangePassword,
} from "../services/authApi";

// -------------------------------------
// Context Initialization
// -------------------------------------
const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// -------------------------------------
// Provider
// -------------------------------------
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [otpState, setOtpState] = useState(null); // { flow, email, password }
  const navigate = useNavigate();

  // Restore user session from stored tokens
  useEffect(() => {
    const access = localStorage.getItem("access");
    if (!access) return;
    getProfile()
      .then(({ data }) => setUser(data))
      .catch(() => logout());
  }, []);

  // ==================================================
  // 🟢 REGISTER FLOW
  // ==================================================
  const registerStart = async ({ email, name, password }) => {
    setLoading(true);
    try {
      await sendRegisterOtp({ email, name, password });
      toast.success(`OTP sent to ${email}`);
      setOtpState({ flow: "register", email, password });
      navigate("/verify-register");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  const registerVerify = async ({ otp }) => {
    if (!otpState?.email || otpState.flow !== "register") {
      toast.error("No registration in progress");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        email: otpState.email,
        otp,
        password: otpState.password,
      };

      const { data } = await verifyRegisterOtp(payload);

      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);

      const profile = await getProfile();
      setUser(profile.data);
      setOtpState(null);
      toast.success("Registration complete!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Invalid OTP or email");
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // 🟢 LOGIN FLOW (Stateless OTP)
  // ==================================================
  const loginStart = async ({ email, password }) => {
    setLoading(true);
    try {
      await sendLoginOtp({ email, password });
      toast.success(`OTP sent to ${email}`);
      setOtpState({ flow: "login", email, password }); // ✅ store credentials for verify
      navigate("/verify-login");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const loginVerify = async ({ otp }) => {
    if (!otpState?.email || otpState.flow !== "login") {
      toast.error("No login in progress");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        email: otpState.email,
        password: otpState.password,
        otp,
      };

      const { data } = await verifyLoginOtp(payload);
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);

      const profile = await getProfile();
      setUser(profile.data);
      setOtpState(null);
      toast.success("Login successful!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  // ==================================================
  // 🟡 OTHER UTILITIES
  // ==================================================
  const resend = async () => {
    if (!otpState?.email) return toast.error("No email to resend OTP to.");
    try {
      await resendOtp({ email: otpState.email });
      toast.success("OTP resent successfully");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not resend OTP");
    }
  };

  const changePassword = async (payload) => {
    try {
      await apiChangePassword(payload);
      toast.success("Password updated successfully");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to change password");
    }
  };

  const logout = () => {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    setUser(null);
    setOtpState(null);
    navigate("/login");
  };

  // Provide everything to context
  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        otpState,
        registerStart,
        registerVerify,
        loginStart,
        loginVerify,
        resend,
        changePassword,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
