"""
Basic API endpoint that will allow us to save files.
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from helpers.book_rec_helpers import *
from typing import List
import shutil

# Keep track of which files
# Note: quite hacky to just temporary in-memory DS
mapping = {
    'books_dataset': "",
    'reviews_dataset': ""
}

# Set up Fast API and allow requests from all sources
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """
    Upload files to server.
    """
    try:
        for file in files:
            # Save the file to a location on the server
            with open(file.filename, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Keep track of correct paths
            if ("data" in file.filename):
                mapping["books_dataset"] = file.filename
            else:
                mapping["reviews_dataset"] = file.filename
    except Exception as e:
        # Return an error response if something goes wrong
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Return a success response
    return {"status": "SUCCESS", "message": "Files uploaded successfully"}

@app.post("/create")
async def create_embeddings():
    """
    Create embeddings under the hood.
    """
    try:
        create_collections(mapping["books_dataset"], mapping["reviews_dataset"])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "message": "Embeddings created successfully"}