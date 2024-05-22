/*
 * Singular page app for Launch Week demo.
 */
import React, { useState, useEffect } from 'react';
import './main.css';
import './styles/home.css';

// Hardcoded return options for demo
const columnsNoShow = ["Nouns", "Title", "Reason for Recommendation", "URL"];
const maxResults = 3;
const id = "523edbb2-40ee-47f2-bb37-285140934791"

const App = () => {
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

  // Handling submission of query
  const testQuerySubmitted = (evt) => {
    evt.preventDefault();
    fetchMatches(evt.target.children.query.value);
  }

  // Function to handle changes in the range input
  const handleRangeChange = (event) => {
    setSatisfactionScore(parseInt(event.target.value));
  };

  // Code to actually handle fetching matches
  const fetchMatches = async (query) => {
    // Set some state for feedback
    setFeedbackQuery(query);
    setIsSearching(true);
    setFeedbackDone(false);

    try {
      // Form request
      const apiUrl = 'http://usekenja.com/api/search/' + id;
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
      const apiUrl = 'http://usekenja.com/api/feedback'
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
    <div className="container">
      <br />
      <h1>🔎 Kenja Demo</h1>
      <br />

      <h2>Your Task</h2>
      <p>We're <a href="http://usekenja.com/">Kenja</a>, and we're building AI search for e-commerce. As part of our product development process, we want your feedback on our core search algorithm, and how it compares to a website's traditional search bar.</p>
      <p>The "search battle" we'll be setting up today is against <a href="https://supost.com/">SUPost</a>, which is basically just a Craigslist for Stanford students. To start:</p>
      <ol>
        <li>Pull up Kenja and SUPost side-by-side.</li>
        <li>We'll give you some ideas of items to search for.</li>
        <li>Search for them using both our search engine and SUPost.</li>
        <li>Fill out this <a href="https://forms.gle/5KdqtQM3n2Q89obi6">form</a> to let us know how we did!</li>
      </ol>

      <div className="alert alert-secondary" role="alert">
        <b>Some things to search for:</b>
        <ul>
          <li>Imagine you moved into a new apartment. Search for some items to fill out your apartment.</li>
          <li>Now you're putting together a computer set-up! Search for some equipment and any gear you'll need.</li>
          <li>Finally, you're getting ready for school. Search for some supplies you'll have to buy for the new year.</li>
        </ul>
      </div>
      <br />

      <h2>Search</h2>
      <p>Enter your query to search across all SUPost Data as of May 8, 2024.</p>
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
  );
};

export default App;
