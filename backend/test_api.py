"""
Basic API endpoint that will allow us to save files.
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from helpers.book_rec_helpers import *
from typing import List
import shutil

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
    try:
        for file in files:
            # Save the file to a location on the server
            with open("data/" + str(file.filename), "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        # Return an error response if something goes wrong
        return JSONResponse(status_code=500, content={"error": str(e)})
    
    # Return a success response
    return {"message": "Files uploaded successfully"}