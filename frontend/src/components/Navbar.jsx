import { Link, useLocation } from 'react-router-dom';
import { Plus, LogOut, User } from 'lucide-react';
import './Navbar.css';

function Navbar({ token, username, onLogout }) {
    const location = useLocation();

    const isActive = (path) => location.pathname === path;

    return (
        <nav className="navbar">
            <div className="navbar-inner">
                <Link to="/" className="navbar-brand">
                    <span className="brand-icon">
                        <Plus size={18} strokeWidth={3} />
                    </span>
                    <span className="brand-text">budgetx</span>
                </Link>

                <div className="navbar-links">
                    <Link to="/" className={`nav-link ${isActive('/') ? 'active' : ''}`}>
                        Home
                    </Link>
                    <a href="/#features" className="nav-link">Features</a>
                    {token && (
                        <Link to="/chat" className={`nav-link ${isActive('/chat') ? 'active' : ''}`}>
                            Chat
                        </Link>
                    )}
                    <a href="/#about" className="nav-link">About</a>

                    {token ? (
                        <div className="nav-user">
                            <span className="nav-username">
                                <User size={14} />
                                {username}
                            </span>
                            <button className="nav-logout" onClick={onLogout}>
                                <LogOut size={14} />
                                Logout
                            </button>
                        </div>
                    ) : (
                        <Link to="/login" className="nav-link nav-login-btn">
                            Login
                        </Link>
                    )}
                </div>
            </div>
        </nav>
    );
}

export default Navbar;
