import React, { useState, useEffect } from 'react';
import { Bar } from 'react-chartjs-2'
import "chart.js/auto";
import '../main.css';
import '../styles/home.css';
import Navbar from '../components/Navbar';

const UsagePage = () => {
    // Set title dynamically
    document.title = "Usage | Kenja";

    // State for usage
    const [results, setResults] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [searchUsage, setSearchUsage] = useState(null);

    // Rendering on startup
    useEffect(() => {
        // Call fetchData function when component mounts
        fetchUsage();
    }, []);

    // Code to actually handle fetching usage
    const fetchUsage = async () => {
        try {
            // Form request
            setIsLoading(true);
            const finalUrl = 'http://127.0.0.1:8000/api/usage';

            // Make request
            const response = await fetch(finalUrl);
            if (!response.ok) {
                throw new Error('Failed to fetch data');
            }
            const result = await response.json();

            // Update state with fetched data
            setResults(result["rows"]);

            // Also update graph
            const dates = result["qpt"].map(data => data[0]);
            const numSearches = result["qpt"].map(data => data[1]);
            const barData = {
                labels: dates,
                datasets: [
                  {
                    label: 'Number of Searches',
                    backgroundColor: 'rgba(75,192,192,0.2)',
                    borderColor: 'rgba(75,192,192,1)',
                    borderWidth: 1,
                    hoverBackgroundColor: 'rgba(75,192,192,0.4)',
                    hoverBorderColor: 'rgba(75,192,192,1)',
                    data: numSearches,
                  },
                ],
              };
            setSearchUsage(barData);
            setIsLoading(false);
        } catch (error) {
            setIsLoading(false);
            console.log("ERROR");
        }
    };

    return (
        <>
            <Navbar />
            <div className="container" id="main-div">
                <div className="header">
                    <h1>Usage</h1>
                    <h3>View usage of search APIs.</h3>
                </div>
                <div className="collections-list">
                    <h2>Daily Usage</h2>
                    <h4>See how often users are using the APIs!</h4>
                    {
                        isLoading ? <div className="spinner-border text-dark" role="status"></div> : <Bar data={searchUsage} /> }
                    <h2>History</h2>
                    <h4>Look at previous searches!</h4>
                    {
                        isLoading ? <div className="spinner-border text-dark" role="status"></div> :
                            <ul className="list-group">
                                <li className="list-group-item list-group-item-secondary">
                                    <div className="row">
                                        <div className="col-sm">
                                            <b>Query</b>
                                        </div>
                                        <div className="col-sm">
                                            <b>Time for Search</b>
                                        </div>
                                    </div>
                                </li>
                                {results.map((option, index) => (
                                    <li key={index} className="list-group-item">
                                        <div className="row">
                                            <div className="col-sm">
                                                {option[1]}
                                            </div>
                                            <div className="col-sm">
                                                {option[2]}
                                            </div>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                    }
                </div>
            </div>
        </>
    );
};

export default UsagePage;