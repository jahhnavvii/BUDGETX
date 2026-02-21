import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Chat from './pages/Chat';
import './App.css';

function App() {
  const [token, setToken] = useState(localStorage.getItem('budgetx_token'));
  const [username, setUsername] = useState(localStorage.getItem('budgetx_user') || '');

  const handleLogin = (newToken, newUsername) => {
    localStorage.setItem('budgetx_token', newToken);
    localStorage.setItem('budgetx_user', newUsername);
    setToken(newToken);
    setUsername(newUsername);
  };

  const handleLogout = () => {
    localStorage.removeItem('budgetx_token');
    localStorage.removeItem('budgetx_user');
    setToken(null);
    setUsername('');
  };

  return (
    <BrowserRouter>
      <Navbar token={token} username={username} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route
          path="/login"
          element={
            token ? <Navigate to="/chat" replace /> : <Login onLogin={handleLogin} />
          }
        />
        <Route
          path="/chat"
          element={
            token ? <Chat token={token} username={username} /> : <Navigate to="/login" replace />
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
