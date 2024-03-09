import './App.css';
import React, { useState } from 'react';


function App() {

  const [results, setResults] = useState([]);

  const exampleQueries = ["A fantasy adventure that has dragons", "A hearwarming love story of two childhood friends",
    "A story about an up and coming basketball team", "A nonfiction novel about the ancient roman empire",
    "An autobiography of a United States President", "A page turner about a war between three nations"];

  const submitExample = (evt) => {
    evt.preventDefault();
    fetchMatches(evt.target.textContent);
  }

  const querySubmitted = (evt) => {
    evt.preventDefault();
    fetchMatches(evt.target.children.query.value);
  }

  const fetchMatches = (query) => {
    // Define scope of the request
    const apiUrl = 'http://127.0.0.1:8000/query';
    const queryValue = query;
    const queryParams = { description: String(queryValue) };
    const queryString = new URLSearchParams(queryParams).toString();
    const finalUrl = `${apiUrl}?${queryString}`;
    console.log(queryValue);

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
      })
      .catch(error => {
        // Log any errors to the console
        console.error('There was a problem with the fetch operation:', error);
      });
  };

  return (
    <div className="container">
      <h1>
        Bookworm
      </h1>
      <h3>
        Looking for a new read? Tell me what you're looking for.
      </h3>
      <div flex-direction='row'>
        <h2>Example:</h2>
        <button type="submit" onClick={submitExample}>{exampleQueries[Math.floor(Math.random() * 6)]}</button>
      </div>
      <form onSubmit={querySubmitted}>
        <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
        <button type="submit" className="btn btn-primary mb-3">Submit</button>
      </form>
      <div>
        <h2>Posts:</h2>
        <ul>
          {results.map(post => (
            <li key={post.title}>
              <h3>{post.title}</h3>
              <p>{post.description}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
