import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1/",
  withCredentials: true, // ✅ Send & receive cookies for OTP session tracking
});

API.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Optional: handle auth or server errors
API.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      console.warn("⚠️ Token expired or invalid. Redirecting to login...");
      localStorage.removeItem("access");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default API;
