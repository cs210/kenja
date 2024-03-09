from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from helpers.book_rec_helpers import find_match

app = FastAPI()

# Allow requests from all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Set up initial query API
@app.get("/query")
async def read_root(description: str):
    return find_match(description)
