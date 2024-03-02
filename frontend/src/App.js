import './App.css';
import React, { useState } from 'react';


function App() {

  const [results, setResults] = useState([]);

  const handleClick = (evt) => {
    evt.preventDefault();
    setResults([evt.target.elements.query.value]);
  }

  return (
    <div className="container">
      <h1>
        Bookworm
      </h1>
      <h3>
        Looking for a new read? Tell me what you're looking for.
      </h3>
      <form onSubmit={handleClick}>
        <input className="form-control" name='query' type="text" placeholder="What are you looking for?" aria-label="default input example"></input>
        <button type="submit" className="btn btn-primary mb-3">Submit</button>
      </form>

      <div>
        {results.map((item, index) => (
          <p key={index}>{item}</p>
        ))}
      </div>
    </div>
  );
}

export default App;
