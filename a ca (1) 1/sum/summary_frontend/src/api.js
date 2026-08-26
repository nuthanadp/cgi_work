const API = "http://localhost:5000";

export const fetchWithToken = async (url, options = {}) => {
  const token = localStorage.getItem("jwtToken");
  
  // Create new Headers object to avoid modifying the original options
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.append("Authorization", `Bearer ${token}`);
  }

  // Do not set Content-Type for FormData, the browser does it automatically with the boundary
  if (!(options.body instanceof FormData)) {
    if (!headers.has("Content-Type")) {
      headers.append("Content-Type", "application/json");
    }
  }

  const response = await fetch(`${API}${url}`, { ...options, headers });

  // If the token is expired or invalid, the backend will send a 401 error
  if (response.status === 401) {
    localStorage.removeItem("jwtToken");
    window.location.href = "/login"; // Force a reload to the login page
    throw new Error("Session expired. Please log in again.");
  }

  return response;
};