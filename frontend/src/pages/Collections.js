import React, { useState, useEffect } from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';

const CollectionsPage = () => {
  // Set title dynamically
  document.title = "All Collections | Kenja";

  // State for keeping track of data
  const [collections, setCollections] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load in API data at runtime
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

    // Call fetchData function when component mounts
    fetchData();
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