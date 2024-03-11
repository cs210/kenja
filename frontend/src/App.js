import './App.css';
import React, { useState } from 'react';

const randomNumber = Math.floor(Math.random() * 4);

function App() {

  // Set title dynamically
  document.title = "Bookworm | Find New Books";

  // Managing state
  const [results, setResults] = useState([]);
  const [spinning, setSpinning] = useState(false);

  // Example prompts for users
  const exampleQueries = ["A fantasy adventure that has dragons", "A hearwarming love story of two childhood friends",
    "A story about an up and coming basketball team", "A nonfiction novel about the Ancient Roman Empire",
    "An autobiography of a United States President", "A page turner about a war between three nations"];
  
  // Hooks for using prompts
  const submitExample = (evt) => {
    evt.preventDefault();
    const inputElement = document.querySelector('input[name="query"]');
    if (inputElement) {
        inputElement.value = evt.target.textContent;
    } else {
        console.error('Input field not found!');
    }
    fetchMatches(evt.target.textContent)
  }

  const querySubmitted = (evt) => {
    evt.preventDefault();
    fetchMatches(evt.target.children.query.value);
  }

  // Fetch the appropriate matches
  const fetchMatches = (query) => {
    // Define scope of the request
    setSpinning(true);
    const apiUrl = 'http://kenja.pro/api';
    const queryValue = query;
    const queryParams = { description: String(queryValue) };
    const queryString = new URLSearchParams(queryParams).toString();
    const finalUrl = `${apiUrl}?${queryString}`;

    // Make the actual request
    fetch(finalUrl)
      .then(response => {
        // Check if the response is successful (status code 200)
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        // Parse the JSON response
        return response.json();
      })
      .then(data => {
        // Update the state with the fetched posts
        setResults(data.metadatas[0]);
        setSpinning(false);
      })
      .catch(error => {
        // Log any errors to the console
        console.error('There was a problem with the fetch operation:', error);
      });
  };

  return (
    <div className="container" id="main-div">
      <div className="header">
        <h1> Bookworm </h1>
        <h3> Find a new read using just a description. </h3>
      </div>
      <div className="examples row" flex-direction='row'>
        <div className="col">
          <button type="submit" className="prompt-button" onClick={submitExample}>{exampleQueries[randomNumber]}</button>
        </div>
        <div className="col">
          <button type="submit" className="prompt-button" onClick={submitExample}>{exampleQueries[randomNumber + 1]}</button>
        </div>
        <div className="col">
          <button type="submit" className="prompt-button" onClick={submitExample}>{exampleQueries[randomNumber + 2]}</button>
        </div>
      </div>
      <form className="search-form" onSubmit={querySubmitted} autocomplete="off">
        <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
        <br />
        <button type="submit" className="btn btn-primary mb-3" id="submit-prompt">Submit</button>
      </form>
      <div className="results">
        { spinning === true && <div className="spinner-border" role="status"></div> }
        { results.length > 0 && <h2>Books:</h2>}
        {results.map(book => (
          <div className="result" key={book.title}>
            <div className="card">
              <div className="card-body">
                <h2 className="book-title">{book.title}</h2>
                <span className="badge text-bg-dark book-category">{book.category}</span>
                <p className="book-details">{book.publisher} · {book.publication_date} · <a href={book.link}>Link</a></p>
                <p className="book-description">{book.description}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
