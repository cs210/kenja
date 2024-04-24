"""
Basic API endpoint that will allow us to save files.
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from helpers.book_rec_helpers import *
from typing import List
from helpers.preprocessing import *

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
async def upload_file(files: List[UploadFile] = File(...)):
    """
    Upload files to server; return exception if unsuccessful
    """
    features = None
    try:
        file_path = upload(files[0])
        features = get_header(file_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"status": "SUCCESS", "features": features}

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