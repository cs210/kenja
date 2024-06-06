import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { auth } from '../firebase';

import '../styles/navbar.css';

function Navbar() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(user => {
      if (user) {
        setIsLoggedIn(true);
      } else {
        setIsLoggedIn(false);
      }
    });

    return () => unsubscribe();
  }, []);

  const handleLogout = async () => {
    try {
      await auth.signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error logging out:', error);
    }
  };

  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
      <a className="navbar-brand" href="/">Kenja</a>
      <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
        <span className="navbar-toggler-icon"></span>
      </button>
      <div className="collapse navbar-collapse" id="navbarNav">
        <ul className="navbar-nav mr-auto">
          <li className="nav-item">
            <a className="nav-link" href="/create">Create</a>
          </li>
          <li className="nav-item active">
            <a className="nav-link" href="/collections">Collections</a>
          </li>
          <li className="nav-item">
            <a className="nav-link" href="/usage">Usage</a>
          </li>
        </ul>
        {/* Conditional rendering of logout/login button */}
        {isLoggedIn ? (
          <button className="btn btn-outline-light" onClick={handleLogout}>Logout</button>
        ) : (
          <a className="btn btn-outline-light" href="/login">Login</a>
        )}
      </div>
    </nav>
  );
}

export default Navbar;
