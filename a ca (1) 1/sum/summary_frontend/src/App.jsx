import React, { useState, useEffect, useContext } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { ProjectProvider, ProjectContext } from "./context/ProjectContext";
import 'react-diff-view/style/index.css';
import Header from "./components/Header";
import LoginPage from "./components/LoginPage";
import RegisterPage from "./components/RegisterPage";
import ProjectHomePage from "./components/ProjectHomePage";
import ProjectDashboard from "./components/ProjectDashboard";
import DocumentAnalyzerPage from "./components/DocumentAnalyzerPage";
import TranscriptAnalyzerPage from "./components/TranscriptAnalyzerPage";
import AgentWorkspace from "./components/AgentWorkspace";
import 'katex/dist/katex.min.css';

import SettingsPage from "./components/SettingsPage"; 
import "./styles/theme.css";
import { Toaster } from "react-hot-toast";

// AppContent no longer needs any theme props
const AppContent = ({ onLogout }) => {
    const { loading, isInitialLoad } = useContext(ProjectContext);

    // Shows a global loading spinner until the initial project data is fetched.
    if (isInitialLoad) {
        return (
            <div className="global-loader">
                <div className="loader"></div>
            </div>
        );
    }

    // Renders the main application routes once data is loaded.
    return (
      <>
        {loading && (
          <div className="global-loader">
            <div className="loader"></div>
          </div>
        )}
        <div className="content-container">
            <Routes>
                <Route path="/" element={<ProjectHomePage />} />
                <Route path="/projects/:projectId" element={<ProjectDashboard />} />
                <Route path="/projects/:projectId/documents" element={<DocumentAnalyzerPage />} />
                <Route path="/projects/:projectId/transcripts" element={<TranscriptAnalyzerPage />} />
                <Route path="/projects/:projectId/workspace" element={<AgentWorkspace />} />
                
                <Route 
                    path="/settings" 
                    element={<SettingsPage onLogout={onLogout} />} 
                />
                
                <Route path="*" element={<Navigate to="/" />} />
            </Routes>
        </div>
      </>
    );
};

const App = () => {
  // --- REMOVED: theme state ---
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("jwtToken"));

  useEffect(() => { 
    // --- UPDATED: Hard-code "light" class and only run once ---
    document.body.className = "light"; 
  }, []);

  // --- REMOVED: handleThemeChange function ---

  const handleLoginSuccess = (token) => {
    localStorage.setItem("jwtToken", token);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('jwtToken');
    setIsLoggedIn(false);
  };

  return (
    <Router>
      <Toaster position="top-center" reverseOrder={false} />
      {isLoggedIn ? (
        <ProjectProvider>
          <div className="app-container">
            {/* --- UPDATED: Removed theme props from Header --- */}
            <Header onLogout={handleLogout} />
            
            {/* --- UPDATED: Removed theme props from AppContent --- */}
            <AppContent onLogout={handleLogout} />
          </div>
        </ProjectProvider>
      ) : (
        <Routes>
          <Route path="/login" element={<LoginPage onLoginSuccess={handleLoginSuccess} />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="*" element={<Navigate to="/login" />} />
        </Routes>
      )}
    </Router>
  );
};

export default App;