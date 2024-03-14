"""
Basic FastAPI Endpoint. Also records hacky telemetry for now.
"""
import csv
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from helpers.book_rec_helpers import find_match

# Set up app and telemetry file
app = FastAPI()
TELEMETRY_FILE = "telemetry.csv"

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Set up initial query API, as well as save telemetry
@app.get("/api")
async def read_root(description: str):
    # Get the current date and time
    current_datetime = datetime.now()
    current_datetime_str = current_datetime.strftime('%Y-%m-%d %H:%M:%S')

    # Write to CSV file
    with open(TELEMETRY_FILE, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([current_datetime_str, description])
    
    # Call API
    return find_match(description, False)
