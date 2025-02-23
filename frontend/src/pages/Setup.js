// Imports
import '../main.css';
import React, { useState, useEffect } from 'react';
import Navbar from '../components/Navbar';
import { auth } from '../firebase';
import { useNavigate } from 'react-router-dom';

/*
 * Describes the core single page web component.
 */
function Setup() {

  // Set title dynamically
  document.title = "Create New Collection | Kenja";

  // State for selected files
  const [selectedFiles, setSelectedFiles] = useState(null);
  const [inPipeline, setInPipeline] = useState(false);

  // State to choose product index
  const [uploadedFile, setUploadedFile] = useState(false);
  const [productIndex, setProductIndex] = useState(null);
  const [allFeatures, setAllFeatures] = useState(null);

  // State for features
  const [features, setFeatures] = useState(null);
  const [selectFeatures, setSelectFeatures] = useState(false);
  const [checkboxes, setCheckboxes] = useState(null);

  // State for creation of embeddings
  const [createEmbeddings, setCreateEmbeddings] = useState(false);
  const [gotSuccess, setGotSuccess] = useState(false);
  const [fileId, setFileId] = useState("");

  // Handle auth
  const navigate = useNavigate();
  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged(user => {
      if (!user) {
        navigate("/login"); // User is logged in
      }
    });

    return () => unsubscribe(); // Cleanup subscription on unmount
  }, []);

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

        // Set all features and set the initial product index
        if (status === 'SUCCESS') {
          setAllFeatures(features);
          setUploadedFile(true);
          setProductIndex(features[0]);
        } else {
          console.error('Failed to fetch data');
        }
      }
    } catch (error) {
      console.error("Error fetching data: ", error);
    }
  };

  /*
   * Handle changes to the select component.
   */
  const handleSelectChange = (event) => {
    setProductIndex(event.target.value);
  };

  /*
   * Send list of selected features to backend.
   */
  const handleProductIndex = async () => {
    // Form a product index dictionary
    const productIndexDict = {
      index: productIndex
    };

    // Do something with the features
    const response = await fetch(
      "http://127.0.0.1:8000/set_index",
      {
        method: 'POST', headers: {
          'Content-Type': 'application/json'
        }, body: JSON.stringify(productIndexDict)
      }
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
      // Set the features
      setFeatures(features);
      setSelectFeatures(true);

      // Specifically: set state of checkboxes
      const initialState = {};
      features.forEach(feature => {
        initialState[feature] = false;
      });
      setCheckboxes(initialState);
    } else {
      console.error('Failed to create embeddings');
    }
  }

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
      {
        method: 'POST', headers: {
          'Content-Type': 'application/json'
        }, body: JSON.stringify(relevantFeatures)
      }
    )

    // Check for success
    if (!response.ok) {
      throw new Error('Network response was not ok');
    }

    // Extract data from response
    const responseData = await response.json();
    const { status, id } = responseData;

    // Set features if successful
    if (status === 'SUCCESS') {
      setGotSuccess(true);
      setFileId(String(id));
    } else {
      console.error('Failed to create embeddings');
    }
  }

  return (
    <>
      <Navbar />
      <div className="container" id="main-div">
        <div className="header">
          <h1>Create New Collection</h1>
          <h3>Set up your dataset to create a new search endpoint.</h3>
        </div>
        <div className="step">
          <h2>Step 1: Upload Your Data</h2>
          <h4>Upload all of your product catalog in the form of csv or text files.</h4>
          <input type="file" accept=".txt, .pdf, .doc, .docx, .csv" multiple onChange={handleFileChange} />
          <button onClick={handleUpload} className="btn btn-dark">Upload</button>
        </div>
        {inPipeline ? <div className="step">
          <h2>Step 2: Sending Over Data</h2>
          <h4>We're first sending over your files to be processed.</h4>
          {allFeatures ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
          </svg>  Successfully uploaded!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}

        {uploadedFile ?
          <div className="step">
            <h2>Step 3: Pick ID of Data</h2>
            <h4>Pick the unique identifier of each of your SKUs.</h4>
            <select
              className="form-select"
              aria-label="Select a product index!"
              value={productIndex}
              onChange={handleSelectChange}
            >
              {allFeatures.map((option, index) => (
                <option key={index} value={option}>{option}</option>
              ))}
            </select>
            <br />
            <button onClick={handleProductIndex} className="btn btn-dark">Submit</button>
          </div> : null}

        {selectFeatures ? <div className="step">
          <h2>Step 4: Select Relevant Features</h2>
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

        {createEmbeddings ? <div className="step">
          <h2>Step 5: Making Product Data Searchable</h2>
          <h4>Next, we're making your data usable for our algorithm.</h4>
          {gotSuccess ? <div className="success"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" className="bi bi-check-circle-fill" viewBox="0 0 16 16">
            <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0m-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z" />
          </svg>  Successfully created embeddings!</div> : <div className="spinner-border text-dark" role="status"></div>}
        </div> : null}

        {gotSuccess ? <div className="step">
          <h2>Step 6: Use Search APIs</h2>
          <h4>Congrats! Your data is now searchable -- try calling one of our REST APIs to try it out!</h4>
          <p>Also, check out <a href={"/collections/" + fileId}>the collection here!</a></p>
        </div> : null}
      </div>
    </>
  );
}

export default Setup;
