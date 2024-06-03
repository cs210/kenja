"""
Basic API endpoint that will allow us to save files.
"""

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from helpers.collection_creation import create_collections
from helpers.db_helpers import create_db, read_all_rows, queries_per_timestamp
from helpers.faf_helpers import find_match, find_chroma_collections, ProductDescription, LOGGING_FILE, EMBEDDINGS_PATH
from helpers.preprocessing import upload, get_header, DATA_PATH
import logging
import os
import re
from typing import List, Dict
import uuid

# Setting up metadata storing, database, and logging
mapping = {}
create_db()
logging.basicConfig(filename=LOGGING_FILE, level=logging.INFO)
LOG_FILE_PATH = "telemetry.log"

# Set up Fast API and allow requests from all sources
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/telemetry")
def get_metrics() -> Dict[str, float]:
    """
    Endpoint that allows us to see number of unique searches, average
    search time, and average satisfaction score.
    """
    # Define initial variables
    unique_searches = set()
    total_search_time = 0.0
    search_count = 0
    total_satisfaction_score = 0.0
    satisfaction_count = 0

    # Open log file and search using regex
    with open(LOG_FILE_PATH, "r") as log_file:
        for line in log_file:
            search_match = re.search(r'User searched collection .+ for query: "(.*?)"', line)
            time_match = re.search(r'Search query ".+?" took ([\d.]+) seconds', line)
            satisfaction_match = re.search(r'Search results for query ".+?" had a satisfaction score of: (\d+)', line)

            # Find matches
            if search_match:
                unique_searches.add(search_match.group(1))

            if time_match:
                total_search_time += float(time_match.group(1))
                search_count += 1

            if satisfaction_match:
                total_satisfaction_score += int(satisfaction_match.group(1))
                satisfaction_count += 1

    # Calculate statistics
    average_search_time = total_search_time / search_count if search_count else 0.0
    average_satisfaction_score = total_satisfaction_score / satisfaction_count if satisfaction_count else 0.0

    # Return statistics
    return {
        "num_unique_searches": len(unique_searches),
        "average_search_time": average_search_time,
        "average_satisfaction_score": average_satisfaction_score
    }

@app.post("/upload")
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Upload files to server; return exception if unsuccessful
    """
    # Generate UUID
    features = None
    new_uuid = str(uuid.uuid4())
    mapping["id"] = new_uuid

    # Try saving file
    try:
        file_path = upload(files[0], new_uuid)
        features, encoding = get_header(file_path)

        # Save features and encoding
        mapping["features"] = features
        mapping["encoding"] = encoding

    # Return error or success depending on status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "features": features}


@app.post("/set_index")
async def set_index(data: dict):
    """
    Set the product index
    """
    # Extract the index and return all other features
    try:
        mapping["index"] = data["index"]

    # Return error or success depending on status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "features": mapping["features"]}


@app.post("/create")
async def create_embeddings(features: List[str]):
    """
    Create embeddings under the hood.
    """
    # Get a list of all the files in the CSV and create collections
    try:
        csv_files = os.listdir(DATA_PATH + mapping["id"])
        csv_files = [DATA_PATH + mapping["id"] + "/" + file for file in csv_files]
        create_collections(
            csv_files, mapping["index"], features, mapping["id"], mapping["encoding"]
        )

    # Return error or success depending on status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "id": mapping["id"]}


@app.get("/collections")
async def get_collections():
    """
    Get list of all collections that a user has created.
    """
    files = os.listdir(EMBEDDINGS_PATH)
    return {"status": "SUCCESS", "files": files}


@app.get("/collections/{id}")
async def read_collection(id: str):
    """
    Get metadata for a collection (to add more features).
    """
    files = os.listdir(DATA_PATH + id)
    return {"status": "SUCCESS", "files": files}


@app.get("/api/search/{id}")
async def search_collection(id: str, query: str):
    """
    Search a specific collection (to add more security).
    """
    # Find all features
    collections = find_chroma_collections(id)
    features = []
    for col in collections:
        if col.name != "middle_collection" and col.name != "Nouns":
            features.append(col.name)

    # Form description and call find match
    description = ProductDescription(
        noun_collection = "Nouns",
        feature_collections=features,
        hidden_collections=[],
        middle_collection="middle_collection",
    )

    # Set up telemetry and find match
    logging.info("User searched collection " + id + ' for query: "' + query + '"')
    results = find_match(query, description, id)
    return {"status": "SUCCESS", "results": results}


@app.get("/api/feedback")
async def obtain_telemetry(query: str, value: str):
    """
    Get telemetry from the frontend
    """
    # Try to log the score to the telemetry log!
    try:
        logging.info(
            'Search results for query "'
            + query
            + '" had a satisfaction score of: '
            + value
        )

    # Return error or success depending on status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS"}

@app.get("/api/usage")
async def retrieve_usage():
    """
    Retrieve usage stats from searches
    """
    # Query database for appropriate statistics
    try:
        data = read_all_rows()
        qpt = queries_per_timestamp()

    # Return error or success depending on status
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "rows": data, "qpt": qpt}
