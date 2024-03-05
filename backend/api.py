from fastapi import FastAPI
from helpers.book_rec_helpers import find_match
app = FastAPI()

@app.get("/query")
async def read_root(description: str):
    return find_match(description)