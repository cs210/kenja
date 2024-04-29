
import '../styles/navbar.css';
import React from 'react';

/*
 * Describes the Navbar for the B2B dashboard.
 */
function Navbar() {
    return (
        <nav className="navbar navbar-expand-lg navbar-dark bg-dark">
            <a className="navbar-brand" href="/">Kenja</a>
            <button className="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span className="navbar-toggler-icon"></span>
            </button>
            <div className="collapse navbar-collapse" id="navbarNav">
                <ul className="navbar-nav">
                <li className="nav-item active">
                    <a className="nav-link" href="/collections">Collections</a>
                </li>
                <li className="nav-item">
                    <a className="nav-link" href="/create">Create New Collection</a>
                </li>
                </ul>
            </div>
        </nav>
)
}

export default Navbar;