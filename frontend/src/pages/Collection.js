import React, { useState, useEffect } from 'react';
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';
import { useParams, useNavigate } from 'react-router-dom';
import { auth } from '../firebase';

// Const number of return options
const columnsNoShow = ["Nouns", "Title", "Reason for Recommendation", "URL"];
const maxResults = 3;

const CollectionPage = () => {
  // Set title dynamically
  document.title = "View Collection | Kenja";
  const { id } = useParams();

  // State for collection
  const [collection, setCollection] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // State for search results
  const [isSearching, setIsSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [isOpen, setIsOpen] = useState(Array(maxResults).fill(false));

  // Feedback for collections
  const [feedbackQuery, setFeedbackQuery] = useState("");
  const [satisfactionScore, setSatisfactionScore] = useState(3);
  const [feedbackDone, setFeedbackDone] = useState(false);

  // Function to toggle the dropdown state of a specific book
  const toggleDropdown = (index) => {
    const updatedOpenState = [...isOpen];
    updatedOpenState[index] = !updatedOpenState[index];
    setIsOpen(updatedOpenState);
  };

  // Function to handle changes in the range input
  const handleRangeChange = (event) => {
    setSatisfactionScore(parseInt(event.target.value));
  };

  // Populate collection page
  const navigate = useNavigate();
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

    const unsubscribe = auth.onAuthStateChanged(user => {
      if (!user) {
        navigate("/login"); // User is logged in
      }
    });

    // Call fetchData function when component mounts
    fetchData();
    return () => unsubscribe(); 
  }, []);

  // Handling submission of query
  const testQuerySubmitted = (evt) => {
    evt.preventDefault();
    fetchMatches(evt.target.children.query.value);
  }

  // Code to actually handle fetching matches
  const fetchMatches = async (query) => {
    // Set some state for feedback
    setFeedbackQuery(query);
    setIsSearching(true);
    setFeedbackDone(false);

    try {
      // Form request
      const apiUrl = 'http://127.0.0.1:8000/api/search/' + id;
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

  // Handling submission of feedback
  const feedbackSubmitted = async (evt) => {
    evt.preventDefault();

    try {
      // Form request
      const apiUrl = 'http://127.0.0.1:8000/api/feedback'
      const queryParams = { query: String(feedbackQuery), value: String(satisfactionScore) };
      const queryString = new URLSearchParams(queryParams).toString();
      const finalUrl = `${apiUrl}?${queryString}`;

      // Make request
      const response = await fetch(finalUrl);
      if (!response.ok) {
        throw new Error('Failed to fetch data');
      }
      const result = await response.json();

      // Update state with fetched data
      setFeedbackDone(true);
    } catch (error) {
      setIsSearching(false);
      console.log("ERROR");
    }
  }

  return (
    <>
      <Navbar />
      <div className="container" id="main-div">
        <div className="header">
          <h1>View Collection</h1>
          <h3>ID: {id}</h3>
        </div>
        <div>
          <h2>Files</h2>
          <h4>View files that are a part of this collection.</h4>
          {isLoading ? <div className="spinner-border text-dark" role="status"></div> : <p><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-file-earmark" viewBox="0 0 16 16">
            <path d="M14 4.5V14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V2a2 2 0 0 1 2-2h5.5zm-3 0A1.5 1.5 0 0 1 9.5 3V1H4a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V4.5z" />
          </svg> {collection["files"]}</p>}
        </div>
        <div>
          <h2>Playground</h2>
          <h4>Experiment with the search before integration!</h4>
          <form className="search-form" onSubmit={testQuerySubmitted} autoComplete="off">
            <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
            <br />
            <button type="submit" className="btn btn-dark" id="submit-prompt">Search</button>
          </form>
          <br />
          {isSearching ? <div className="spinner-border text-dark" role="status"></div> :
            <>
              {results ?
                <>
                  <h3>Results</h3>
                  <div className="collections-list">
                    <ul className="list-group">
                      {results.map((option, index) => (
                        <li key={index} className="list-group-item">
                          <h4 className="option-title">{option["Title"]} · <a className="result-link" href={option["URL"]}>🔗</a></h4>
                          <p>{option["Reason for Recommendation"]}</p>
                          <button
                            className="description-button dropdown-toggle"
                            type="button"
                            onClick={() => toggleDropdown(index)}
                            aria-expanded={isOpen[index] ? "true" : "false"}
                            aria-controls={"collapse" + option["Title"]}
                            data-bs-toggle="dropdown"
                          >
                            <b>View Information</b>
                          </button>
                          <div className={`collapse ${isOpen[index] ? 'show' : ''}`} id={"collapse" + option["Title"]}>
                            <ul>
                              {Object.keys(option)
                                .filter((key) => !columnsNoShow.includes(key))
                                .map((key) => (
                                  <li key={key}>
                                    <span>
                                      <b>{key}:</b> {option[key]}
                                      <br />
                                    </span>
                                  </li>
                                ))}
                            </ul>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <br />
                  <h3>How satisfied were you with these results?</h3>
                  {feedbackDone ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
                    <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
                  </svg>  Successfully submitted feedback!</div> : <>
                    <h5>Satisfaction Score: <b>{satisfactionScore}</b></h5>
                    <input
                      type="range"
                      className="form-range"
                      min="1"
                      max="5"
                      id="satisfaction-score"
                      value={satisfactionScore}
                      onChange={handleRangeChange}
                    />
                    <form className="search-form" onSubmit={feedbackSubmitted} autoComplete="off">
                      <button type="submit" className="btn btn-dark" id="submit-feedback">Send Feedback</button>
                    </form> </>}
                  <br />
                </> : null}
            </>
          }
        </div>
      </div>
    </>
  );
};

export default CollectionPage;