import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1/",
  headers: { "Content-Type": "application/json" },
});

// ====================================================
// 🔹 Add access token to all outgoing requests
// ====================================================
API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ====================================================
// 🔹 REGISTER APIs
// ====================================================
export const sendRegisterOtp = (data) =>
  API.post("users/register/send-otp/", data);

export const verifyRegisterOtp = (data) =>
  API.post("users/register/verify-otp/", data);

// ====================================================
// 🔹 LOGIN APIs
// ====================================================
export const sendLoginOtp = (data) =>
  API.post("users/login/", data);

export const verifyLoginOtp = (data) =>
  API.post("users/login/verify-otp/", data);

// ====================================================
// 🔹 RESEND OTP
// ====================================================
export const resendOtp = (data) =>
  API.post("users/resend-otp/", data);

// ====================================================
// 🔹 PROFILE MANAGEMENT
// ====================================================
export const getProfile = () => API.get("users/profile/");

export const changePassword = (data) =>
  API.patch("users/change-password/", data);
