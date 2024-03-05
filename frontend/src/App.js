import './App.css';
import React, { useState } from 'react';


function App() {

  const [results, setResults] = useState([]);

  const fetchMatches = (evt) => {
    // Define scope of the request
    evt.preventDefault();
    const apiUrl = 'http://127.0.0.1:8000/query';
    const queryValue = evt.target.children.query.value;
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
      <form onSubmit={fetchMatches}>
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
