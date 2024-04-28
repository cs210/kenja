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

  // State for features
  const [features, setFeatures] = useState(null);
  const [selectFeatures, setSelectFeatures] = useState(false);
  const [checkboxes, setCheckboxes] = useState(null);

  // State for creation of embeddings
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
  const handleUpload = async () => {
    try {
      // Load in form data
      if (selectedFiles) {
        const formData = new FormData();
        Array.from(selectedFiles).forEach((file) => {
          formData.append('files', file);
        });

        // Set generation step on and submit to backend
        setInPipeline(true);
        console.log(formData);
        const response = await fetch(
          "http://127.0.0.1:8000/upload", 
          { method: 'POST', body: formData }
        )

        // Check for success
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        
        // Extract data from response
        const responseData = await response.json();
        const { status, features } = responseData;

        // Set features if successful
        if (status === 'SUCCESS') {
          setSelectFeatures(true);
          setFeatures(features);

          // Specifically: set state of checkboxes
          const initialState = {};
          features.forEach(feature => {
            initialState[feature] = false;
          });
          setCheckboxes(initialState);
        } else {
          console.error('Failed to fetch data');
        }
      }
    } catch (error) {
      console.error("Error fetching data: ", error);
    }
  };

  /*
   * Handle changes to any checkboxes.
   */
  const handleCheckboxChange = (event) => {
    const { name, checked } = event.target;
    setCheckboxes({
      ...checkboxes,
      [name]: checked
    });
  };

  /*
   * Send list of selected features to backend.
   */
  const handleFeatures = async () => {
    // Extract the picked features
    setCreateEmbeddings(true);
    const relevantFeatures = Object.entries(checkboxes)
      .filter(([key, value]) => value === true)
      .map(([key, value]) => key);

    // Do something with the features
    const response = await fetch(
      "http://127.0.0.1:8000/create", 
      { method: 'POST', headers: {
        'Content-Type': 'application/json'
      }, body: JSON.stringify(relevantFeatures) }
    )

    // Check for success
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }
    
    // Extract data from response
    const responseData = await response.json();
    const { status } = responseData;

    // Set features if successful
    if (status === 'SUCCESS') {
      setGotSuccess(true);
    } else {
      console.error('Failed to create embeddings');
    }
  }

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
        { selectFeatures ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
</svg>  Successfully uploaded!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}

      { selectFeatures ? <div className="step">
      <h2>Step 3: Select Relevant Features</h2>
      <h4>Pick the features below you think are most important to your products.</h4>
      {features.map((option, index) => (
        <div key={index} className="form-check">
          <input
            type="checkbox"
            className="form-check-input"
            id={option}
            name={option}
            checked={checkboxes[option]}
            onChange={handleCheckboxChange}
          />
          <label className="form-check-label" htmlFor={option}>
            {option}
          </label>
        </div>
      ))}
      <br />
      <button onClick={handleFeatures} className="btn btn-dark">Submit</button>
      </div> : null}

        { createEmbeddings ? <div className="step">
        <h2>Step 4: Making Product Data Searchable</h2>
        <h4>Next, we're making your data usable for our algorithm.</h4>
        { gotSuccess ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
  <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z"/>
</svg>  Successfully created embeddings!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}
        { gotSuccess ? <div className="step">
        <h2>Step 5: Use Search APIs</h2>
        <h4>Congrats! Your data is now searchable -- try calling one of our REST APIs to try it out!</h4>
        </div> : null}
    </div>
  );
}

export default App;
