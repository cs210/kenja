import React, { useState, useEffect } from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';

const CollectionsPage = () => {
  // Set title dynamically
  document.title = "All Collections | Kenja";

  // State for keeping track of data
  const [collections, setCollections] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load in API data at runtime
  const navigate = useNavigate();
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Set loading state
        setIsLoading(true);

        // Fetch data from the API
        const response = await fetch('http://127.0.0.1:8000/collections');
        if (!response.ok) {
          throw new Error('Failed to fetch data');
        }
        const result = await response.json();

        // Update state with fetched data
        setCollections(result['files']);
        setIsLoading(false);
      } catch (error) {
        // Handle errors
        setIsLoading(false);
      }
    };

    const unsubscribe = auth.onAuthStateChanged(user => {
      if (!user) {
        navigate("/login"); // User is logged in
      }
    });

    // Call fetchData function when component mounts
    fetchData();
    return () => unsubscribe(); 
  }, []);


  return (
    <>
      <Navbar />
      <div className="container" id="main-div">
        <div className="header">
          <h1>All Collections</h1>
          <h3>View all existing collections!</h3>
        </div>
        {isLoading ? <div className="spinner-border text-dark" role="status"></div> :
          <div className="collections-list">
            <ul className="list-group">
              {collections.map((option, index) => (
                <li key={index} className="list-group-item">
                  <a href={"/collections/" + option}>{option}</a>
                </li>
              ))}
            </ul>
          </div>}
      </div>
    </>
  );
};

export default CollectionsPage;