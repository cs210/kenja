"""
Sample code for noun parsing!
"""
import torch
if torch.cuda.is_available():
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import chromadb
from chromadb.config import Settings

import spacy
import pandas as pd
import uuid
import time

from faf_helpers import *
from tqdm import tqdm


nlp = spacy.load("en_core_web_sm")


def find_nouns(text: str):
    """
    Given a certain string, find all the nouns in the string
    """
    doc = nlp(text)
    nouns = []
    for token in doc:
        if token.pos_ == "NOUN":
            nouns.append(token.text)
    return nouns


def apply_nouns(series):
    """
    Across a row of a CSV file, find all the nouns across all column contents!
    """
    all_nouns = []
    for _, value in series.items():
        val_str = str(value)
        nouns = find_nouns(val_str)
        all_nouns.extend(nouns)
    return " ".join(all_nouns)


def add_nouns(df):
    """
    Add nouns to dataframe
    """
    nouns_col = df.apply(lambda row: apply_nouns(row), axis=1)
    df["Nouns"] = nouns_col
    return df

def keyword_search_nouns(df, query):
    """
    Search for nouns in query
    """
    nouns = find_nouns(query)
    df = pd.read_csv("nouns_supost_clean.csv")
    search_string = nouns[0]
    result_series = df["Nouns"].apply(lambda x: search_string in x)
    result_rows = df[result_series]
    print(result_rows)

def create_embeddings(df):
    """
    Create personal embeddings :D
    """
    # Create a chroma client
    file_id = str(uuid.uuid1())
    chroma_client = chromadb.PersistentClient(
        path="./embeddings/nouns/" + file_id, settings=Settings(anonymized_telemetry=False)
    )
    noun_collection = chroma_client.create_collection(name="nouns")

    # Iterate through all rows
    rows = list(df.iterrows())
    for i in tqdm(range(0, len(rows), 5), desc="Noun Embeddings Creation"):

        # Find start and stop
        start, stop = i, min(i+5, len(rows))
        subset = rows[start:stop]

        # Get metadatas, IDs, and nouns
        metadatas = [row[1].to_dict() for row in subset]
        ids = [str(metadata['Unnamed: 0']) for metadata in metadatas]
        nouns = df[start:stop]['Nouns'].tolist()

        # Generate embeddings
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        embeddings = open_source_create_embeddings(nouns, True)
        noun_collection.add(
            embeddings=embeddings.tolist(),
            documents=nouns,
            metadatas=metadatas, # filter on arbitrary metadata!
            ids=ids, # must be unique for each doc 
        )
    
    # Return collection!!!
    return noun_collection

def semantic_search_nouns(query, collection):
    """
    Semantically search across nouns
    """
    nouns = find_nouns(query)
    # Only have the nouns of the original query be used in the searching
    query = " ".join(nouns)
    embedding = open_source_create_embeddings([query], False)
    results = collection.query(
        query_embeddings=embedding.tolist(),
        n_results=10,
    )

if __name__ == "__main__":
    """
    Just running a bunch of random functions
    """
    # Keyword search stuff
    # query = "I want something for my bedroom"
    # df = pd.read_csv("nouns_supost_clean.csv")
    # keyword_search_nouns(df, query)

    # Semantic stuff
    df = pd.read_csv("nouns_supost_clean.csv")
    noun_collection = create_embeddings(df)
    semantic_search_nouns("I want a cool shirt!", noun_collection)