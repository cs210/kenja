import './App.css';
import React, { useState } from 'react';


function App() {

  const [results, setResults] = useState([]);


  const fetchPosts = (evt) => {
    evt.preventDefault()
    // Define the URL of the API
    const apiUrl = 'https://jsonplaceholder.typicode.com/posts';

    // Make a GET request to the API using fetch
    fetch(apiUrl)
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
        setResults(data);
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
      <form onSubmit={fetchPosts}>
        <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
        <button type="submit" className="btn btn-primary mb-3">Submit</button>
      </form>

      <div>
        <h2>Posts:</h2>
        <ul>
          {results.map(post => (
            <li key={post.id}>
              <h3>{post.title}</h3>
              <p>{post.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
