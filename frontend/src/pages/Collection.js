import React, { useState, useEffect } from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';
import { useParams } from 'react-router-dom';

const CollectionPage = () => {
    // Set title dynamically
    document.title = "View Collection | Kenja";
    const { id } = useParams();

    // State for collection
    const [collection, setCollection] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSearching, setIsSearching] = useState(false);
    const [results, setResults] = useState(null);

    // Populate collection page
    useEffect(() => {
        const fetchData = async () => {
          try {
            // Set loading state
            setIsLoading(true);
    
            // Fetch data from the API
            const response = await fetch('http://127.0.0.1:8000/collections/' + id);
            if (!response.ok) {
              throw new Error('Failed to fetch data');
            }
            const result = await response.json();
    
            // Update state with fetched data
            setCollection(result);
            setIsLoading(false);
          } catch (error) {
            // Handle errors
            setIsLoading(false);
          }
        };
    
        // Call fetchData function when component mounts
        fetchData();
      }, []); 

    // Handling submission of query
    const testQuerySubmitted = (evt) => {
        evt.preventDefault();
        fetchMatches(evt.target.children.query.value);
    }

    // Code to actually handle fetching matches
    const fetchMatches = async (query) => {
        setIsSearching(true);
        try {
            // Form request
            const apiUrl = 'http://127.0.0.1:8000/search/' + id;
            const queryValue = query;
            const queryParams = { query: String(queryValue) };
            const queryString = new URLSearchParams(queryParams).toString();
            const finalUrl = `${apiUrl}?${queryString}`;

            // Make request
            const response = await fetch(finalUrl);
            if (!response.ok) {
              throw new Error('Failed to fetch data');
            }
            const result = await response.json();
    
            // Update state with fetched data
            setResults(result["results"]);
            setIsSearching(false);
          } catch (error) {
            setIsSearching(false);
            console.log("ERROR");
          }
    };

    return (
    <>
        <Navbar />
        <div className="container" id="main-div">
            <div className="header">
                <h1>View Collection</h1>
                <h3>ID: { id }</h3>
            </div>
            <div>
                <h2>Files</h2>
                <h4>View files that are a part of this collection.</h4>
                { isLoading ?  <div className="spinner-border text-dark" role="status"></div> : <p><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-file-earmark" viewBox="0 0 16 16">
  <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z"/>
</svg> {collection["files"]}</p> }
            </div>
            <div>
                <h2>Playground</h2>
                <h4>Experiment with the search before integration!</h4>
                <form className="search-form" onSubmit={testQuerySubmitted} autoComplete="off">
                    <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
                    <br />
                    <button type="submit" className="btn btn-dark" id="submit-prompt">Submit</button>
                </form>
                <br />
                { isSearching ? <div className="spinner-border text-dark" role="status"></div> : 
                  <>
                  { results ? <div className="collections-list">
                <ul className="list-group">
                    { results.map((option, index) => (
                        <li key={index} className="list-group-item">
                          <h3>{option["ProductName"]}</h3>
                          <p>{option["gpt_review"]}</p>
                          <p><b>Description:</b> {option["Description"]}</p>
                        </li>
                    ))}
                </ul>
            </div> : null }
                  </>
                }
            </div>
        </div>
    </>
    );
};

export default CollectionPage;