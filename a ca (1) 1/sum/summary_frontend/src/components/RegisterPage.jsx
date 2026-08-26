import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import toast from 'react-hot-toast';
import "../styles/LoginPage.css"; // We can reuse the same styles

const RegisterPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      toast.error("Passwords do not match!");
      return;
    }
    
    setLoading(true);
    const toastId = toast.loading('Creating account...');

    try {
      const response = await fetch("http://localhost:5000/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(data.message || "Registration successful! Please log in.", { id: toastId });
        navigate("/login"); // Redirect to login page on success
      } else {
        toast.error(data.error || "Registration failed.", { id: toastId });
      }
    } catch (err) {
      toast.error("Error connecting to server: " + err.message, { id: toastId });
    } finally {
        setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="logo-section">
          <img
            src="https://hackerx.org/wp-content/uploads/2021/09/2560px-CGI_logo.svg.png"
            alt="CGI Logo"
            className="logo"
          />
          <span className="system-name">AI SUMMARY AGENT</span>
        </div>
        <h2 className="welcome-text">Create a New Account</h2>

        <form onSubmit={handleRegister} className="login-form">
          <div className="input-group">
            <label htmlFor="email">Email address*</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="john.smith@cgi.com"
              required
            />
          </div>

          <div className="input-group">
            <label htmlFor="password">Password*</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <div className="input-group">
            <label htmlFor="confirm-password">Confirm Password*</label>
            <input
              type="password"
              id="confirm-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />
          </div>

          <button type="submit" className="login-button" disabled={loading}>
            {loading ? "Registering..." : "Register"}
          </button>
        </form>

        <p className="forgot-password">
          Already have an account? <Link to="/login">Login here</Link>
        </p>

        <footer className="footer-text">© CGI Inc. All rights reserved.</footer>
      </div>
      <div className="background-pattern"></div>
    </div>
  );
};

export default RegisterPage;
