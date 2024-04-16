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
        // Handle response
      })
      .catch(error => {
        // Handle error
      });
    }
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
      { inPipeline === true && <div className="step">
        <h2>Step 2: Generating Search APIs</h2>
        <h4>Hang tight: our pipeline is currently generating your search APIs.</h4>
        <div className="spinner-border text-dark" role="status">
        </div>
      </div> }
    </div>
  );
}

export default App;
