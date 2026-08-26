import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; // Import useNavigate
import toast from 'react-hot-toast'; // Import toast
import "../styles/LoginPage.css";

const LoginPage = ({ onLoginSuccess }) => {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [showPassword, setShowPassword] = useState(false);
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate(); // Initialize navigate hook

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await fetch("http://localhost:5000/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            const data = await response.json();

            if (response.ok) {
                localStorage.setItem("jwtToken", data.token);

                // Use toast for success message
                toast.success(data.message || "Login successful!");

                onLoginSuccess(data.token); // Call the success handler

                // Redirect immediately after success
                navigate('/'); // Redirect to the project home page

                return; // Exit after navigation

            } else {
                // Use toast for error message
                toast.error(data.error || "Login failed");
            }
        } catch (err) {
            // Use toast for network error message
            toast.error("Error connecting to server: " + err.message);
        }

        setLoading(false); // Only set loading false on error
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
                <h2 className="welcome-text">Welcome Back</h2>

                <form onSubmit={handleLogin} className="login-form">
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

                    <div className="input-group password-group">
                        <label htmlFor="password">Password*</label>
                        <input
                            type={showPassword ? "text" : "password"}
                            id="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                        <span
                            className="password-toggle"
                            onClick={() => setShowPassword(!showPassword)}
                        >
                            <img
                                src={
                                    showPassword
                                        ? "https://img.icons8.com/material-outlined/24/000000/invisible.png"
                                        : "https://img.icons8.com/material-outlined/24/000000/visible--v1.png"
                                }
                                alt="toggle visibility"
                            />
                        </span>
                    </div>

                    <button type="submit" className="login-button" disabled={loading}>
                        {loading ? "Logging in..." : "Login"}
                    </button>
                </form>

                <footer className="footer-text">© CGI Inc. All rights reserved.</footer>
            </div>

            <div className="background-pattern"></div>
        </div>
    );
};

export default LoginPage;
