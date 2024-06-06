// Imports
import React, { useState, useEffect } from 'react';
import { signInWithEmailAndPassword, onAuthStateChanged, signOut } from 'firebase/auth';
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';

// Visual imports
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';

function LoginPage() {
    // Set title dynamically
    document.title = "Login | Kenja";

    // State
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [user, setUser] = useState(null);
    const navigate = useNavigate();

    // Set the user if we have one
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, (user) => {
            setUser(user);
        });

        // Cleanup subscription on unmount
        return () => unsubscribe();
    }, []);

    // Login the user and redirect if successful
    const handleLogin = async () => {
        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            navigate('/');
        } catch (error) {
            // Throw error otherwise
            console.error('Error logging in:', error);
        }
    };

    // Logout the user
    const handleLogout = async () => {
        try {
            await signOut(auth);
        } catch (error) {
            console.error('Error logging out:', error);
        }
    };

    return (
        <>
            <Navbar />
            <div className="container" id="main-div">
                {!user ? (
                    <>
                        <div className="header">
                            <h1>Login</h1>
                            <h3>Log into your account.</h3>
                        </div>

                        <h2>Email</h2>
                        <input
                            type="email"
                            className="form-control"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Email"
                        />
                        <br />

                        <h2>Password</h2>
                        <input
                            type="password"
                            className="form-control"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Password"
                        />
                        <br />
                        <button className="btn btn-dark" onClick={handleLogin}>Login</button>
                    </>
                ) : (
                    <>
                        <div className="header">
                            <h1>You're already logged in!</h1>
                            <h3>Go to your <a href="/">account</a>.</h3>
                        </div>
                    </>
                )}
            </div>
        </>
    );
}

export default LoginPage;
