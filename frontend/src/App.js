import './App.css';
import React, { useState } from 'react';

/*
 * Describes the core single page web component.
 */
function App() {

  // Set title dynamically
  document.title = "Setup | Kenja";

  // State for selected files
  const [selectedFiles, setSelectedFiles] = useState(null);
  const [inPipeline, setInPipeline] = useState(false);
  const [createEmbeddings, setCreateEmbeddings] = useState(false);
  const [gotSuccess, setGotSuccess] = useState(false);

  /*
   * Set the updated product catalog files.
   */
  const handleFileChange = (event) => {
    setSelectedFiles(event.target.files);
  };

  /*
   * Upload files to the backend.
   */
  const handleUpload = () => {
    // Create a new data structure with the files
    if (selectedFiles) {
      const formData = new FormData();
      Array.from(selectedFiles).forEach((file) => {
        formData.append('files', file);
      });

      // Set generation step on and submit to backend
      setInPipeline(true);
      fetch("http://127.0.0.1:8000/upload", {
        method: 'POST',
        body: formData,
      })
      .then(response => {
        // If we got a good response, then we can start creating embeddings!
        if (response.ok) {
          setCreateEmbeddings(true);
          callCreate();
        }
      })
      .catch(error => {
        // Handle error
      });
    }
  };

  /*
   * Upload files to the backend.
   */
  const callCreate = () => {
    // Set embeddings step on and submit to backend
    setCreateEmbeddings(true);
    fetch("http://127.0.0.1:8000/create", {
      method: 'POST',
    })
    .then(response => {
      // If we got a good response, then we can start creating embeddings!
      if (response.ok) {
        setGotSuccess(true);
      }
    })
    .catch(error => {
      // Handle error
    });
  };

  return (
    <div className="container" id="main-div">
      <div className="header">
        <h1>Set-Up</h1>
        <h3>Set up your dataset to create a new search endpoint.</h3>
      </div>
      <div className="step">
        <h2>Step 1: Upload Your Data</h2>
        <h4>Upload all of your product catalog in the form of csv or text files.</h4>
        <input type="file" accept=".txt, .pdf, .doc, .docx" multiple onChange={handleFileChange} />
        <button onClick={handleUpload} className="btn btn-dark">Upload</button>
      </div>
      { inPipeline ? <div className="step">
        <h2>Step 2: Sending Over Data</h2>
        <h4>We're first sending over your files to be processed.</h4>
        { createEmbeddings ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
</svg>  Successfully uploaded!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}
        { createEmbeddings ? <div className="step">
        <h2>Step 3: Making Product Data Searchable</h2>
        <h4>Next, we're making your data usable for our algorithm.</h4>
        { gotSuccess ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
</svg>  Successfully created embeddings!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}
        { gotSuccess ? <div className="step">
        <h2>Step 4: Use Search APIs</h2>
        <h4>Congrats! Your data is now searchable -- try calling one of our REST APIs to try it out!</h4>
        </div> : null}
    </div>
  );
}

export default App;
