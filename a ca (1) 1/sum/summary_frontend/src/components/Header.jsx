import React, { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
// --- UPDATED: Removed Sun and Moon ---
import { LogOut, User, Settings } from 'lucide-react';
import { jwtDecode } from 'jwt-decode';

// --- UPDATED: Removed theme and setTheme props ---
const Header = ({ onLogout }) => {
    const [isDropdownOpen, setIsDropdownOpen] = useState(false);
    const [userInfo, setUserInfo] = useState({
        email: 'Loading...',
        username: 'User',
        initials: 'U'
    });
    const dropdownRef = useRef(null);

    const getInitials = (email) => {
        // ... (getInitials function remains the same)
        if (!email) return 'U';
        const emailParts = email.split('@')[0];
        const names = emailParts.split('.');
        if (names.length > 1 && names[0][0] && names[1][0]) { return (names[0][0] + names[1][0]).toUpperCase(); }
        else if (emailParts.length > 1) { return (emailParts[0] + emailParts[1]).toUpperCase(); }
        else if (emailParts.length > 0) { return emailParts[0].toUpperCase(); }
        return 'U';
    };

    useEffect(() => {
        const token = localStorage.getItem('jwtToken');
        if (token) {
            try {
                const decoded = jwtDecode(token);
                const userEmail = decoded.email || 'N/A';
                const initials = getInitials(userEmail);
                setUserInfo({ email: userEmail, username: userEmail.split('@')[0] || 'User', initials: initials });
            } catch (error) {
                console.error("Failed to decode token:", error);
                setUserInfo({ email: 'Error', username: 'User', initials: 'E' });
            }
        } else {
             setUserInfo({ email: 'Not logged in', username: 'Guest', initials: 'G' });
        }
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsDropdownOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const toggleDropdown = () => setIsDropdownOpen(!isDropdownOpen);
    const handleLogoutClick = () => { setIsDropdownOpen(false); onLogout(); };

    return (
        <header className="header-container">
            {/* Logo Section */}
            <Link to="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center' }}>
                <span className="header-logo">CGI</span>
                <span className="header-divider">|</span>
                <span className="header-title">RADAR – Requirements Analysis & Documentation Auto-Refiner</span>
                 <span style={{ marginLeft: '10px', display: 'flex', gap: '5px' }}></span>
            </Link>

            {/* Actions Section */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                
                {/* --- REMOVED: Theme Toggle Button --- */}

                {/* Profile Menu */}
                <div className="profile-menu-container" ref={dropdownRef}>
                    <button onClick={toggleDropdown} className="profile-button" aria-label="User menu">
                        <User size={18} />
                    </button>

                    {/* --- UPDATED DROPDOWN STRUCTURE --- */}
                    <div className={`profile-dropdown ${isDropdownOpen ? 'show' : ''}`}>
                        {/* Centered User Info */}
                        <div className="dropdown-user-info centered">
                            <div className="profile-avatar">{userInfo.initials}</div>
                            <div className="profile-user-text">
                                <p className="username">{userInfo.username}</p>
                                <p className="email">{userInfo.email}</p>
                            </div>
                        </div>
                        {/* Action List */}
                        <ul className="dropdown-menu-list clean-list">
                            <li>
                                <Link to="/settings" className="dropdown-menu-item" onClick={() => setIsDropdownOpen(false)}>
                                    <Settings size={16} /> Settings
                                </Link>
                            </li>
                            <li>
                                {/* Use a div styled like a button for logout */}
                                <div onClick={handleLogoutClick} className="dropdown-menu-item logout-item">
                                    <LogOut size={16} /> Logout
                                </div>
                            </li>
                        </ul>
                    </div>
                     {/* --- END OF UPDATE --- */}
                </div>
            </div>
        </header>
    );
};

export default Header;