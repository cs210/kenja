// Imports
import React, { useEffect } from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';

const HomePage = () => {
    // Set title dynamically
    document.title = "Home | Kenja";

    // Handle auth
    const navigate = useNavigate();
    useEffect(() => {
        const unsubscribe = auth.onAuthStateChanged(user => {
            if (!user) {
                navigate("/login"); // User is logged in
            }
        });

        return () => unsubscribe(); // Cleanup subscription on unmount
    }, []);

    return (
        <>
            <Navbar />
            <div className="container" id="main-div">
                <div className="header">
                    <h1>Welcome back to Kenja!</h1>
                    <h3>Look through existing collections or create a new one!</h3>
                </div>

                <div className="row">
                    <div className="col-sm">
                        <a className="option-link" href="/collections">
                            <div className="card">
                                <div className="card-body">
                                    All Collections
                                </div>
                            </div>
                        </a>
                    </div>
                    <div className="col-sm">
                        <a className="option-link" href="/create">
                            <div className="card">
                                <div className="card-body">
                                    Create New Collection
                                </div>
                            </div>
                        </a>
                    </div>
                    <div className="col-sm">
                        <a className="option-link" href="/usage">
                            <div className="card">
                                <div className="card-body">
                                    View Usage
                                </div>
                            </div>
                        </a>
                    </div>
                </div>
            </div>
        </>
    );
};

export default HomePage;
