import React from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';

const HomePage = () => {
    // Set title dynamically
    document.title = "Home | Kenja";

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
                        <a className="option-link" href="http://kenja.pro/">
                            <div className="card">
                                <div className="card-body">
                                    Get Support
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