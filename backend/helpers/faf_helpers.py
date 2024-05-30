"""
Helper functions to assist with the Find and Filter algorithm.
"""

from venv import create
import torch

from .embedding_creation import  open_source_create_embeddings, create_collection_embeddings

# For chromadb with Chris's GPU
if torch.cuda.is_available():
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

# For help with generation
from .generation_helpers import get_generation

# For making embeddings and such
import chromadb
from chromadb.config import Settings
from datetime import datetime
from .db_helpers import add_query
from dotenv import load_dotenv
import logging
import uuid
import time
from typing import List

# Constants
LOGGING_FILE = "telemetry.log"
logging.basicConfig(filename=LOGGING_FILE, level=logging.INFO)

OPTION_COUNT = 10

load_dotenv()
EMBEDDINGS_PATH = "./embeddings/"


def embedding_search(collection, query, n_results):
    embedding = open_source_create_embeddings([query], False).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n_results)
    return results


def find_chroma_collections(file_id):
    """
    Helper function to get a list of all collections.
    """
    chroma_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )
    return chroma_client.list_collections()


# Contains names of relevant collections
class ProductDescription:
    def __init__(
        self,
        noun_collection: List[str],
        feature_collections: List[str],
        hidden_collections: List[str],
        middle_collection: str,
    ):
        self.feature_collections = feature_collections
        self.hidden_collections = hidden_collections
        self.middle_collection = middle_collection


def find_match(query, product_description: ProductDescription, file_id):
    """
    Call all functions.
    """
    # Record the start time
    start_time = time.time()

    # Create chroma and temp clients for specific file
    chroma_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )
    temp_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )

    noun_collection = chroma_client.get_collection(
        name="Nouns"
    )

    # Create all feature collections
    feature_collections = []
    for collection in product_description.feature_collections:
        feature_collections.append(chroma_client.get_collection(name=collection))
    for collection in product_description.hidden_collections:
        feature_collections.append(chroma_client.get_collection(name=collection))

    middle_collection = chroma_client.get_collection(
        name=product_description.middle_collection
    )

    # Noun level
    noun_search_results = embedding_search(
        noun_collection, query, min(150, int(0.05 * noun_collection.count()))
    )
    nouns_ids_list = []
    for i in range(len(noun_search_results["metadatas"][0])):
        nouns_ids_list.append(str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{noun_search_results['metadatas'][0][i]['VALUE_ID'], noun_search_results['documents'][0][i]}")))
    nouns_ids_list = list(
        set(nouns_ids_list)
    )


    extract_dict = feature_collections[0].get(
        ids=nouns_ids_list, include=["embeddings", "documents", "metadatas"]
    )

    # FIRST LEVEL
    ids_list = []
    for feature_collection in feature_collections:
        client_name = str(uuid.uuid1())
        extract_dict = feature_collection.get(
            ids=nouns_ids_list, include=["embeddings", "documents", "metadatas"]
        )
        extract_collection = temp_client.create_collection(name=client_name)
        extract_collection.add(
            embeddings=extract_dict["embeddings"],
            documents=extract_dict["documents"],
            metadatas=extract_dict["metadatas"],
            ids=extract_dict["ids"],
        )

        partial_search_results = embedding_search(
            extract_collection, query, min(20, int(0.05 * extract_collection.count()))
        )
        partial_ids_list = [
            str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{dictionary['VALUE_ID']}"))
            for dictionary in partial_search_results["metadatas"][0]
        ]
        partial_ids_list = list(
            set(partial_ids_list)
        )  # there is a chance that the same id will appear multiple times
        ids_list.extend(partial_ids_list)
        ids_list = list(set(ids_list))
        temp_client.delete_collection(name=client_name)

    # SECOND LEVEL
    extract_dict = middle_collection.get(
        ids=ids_list, include=["embeddings", "documents", "metadatas"]
    )
    
    """
    Below is the code for the new middle collection where teh query is appended.
    """
    middle_documents = extract_dict["documents"]
    middle_documents = ["Query: " + query + "\n\n" + entry for entry in middle_documents]
    client_name = str(uuid.uuid1())
    extract_collection = temp_client.create_collection(name=client_name)
    create_collection_embeddings(extract_collection, "middle text", middle_documents, extract_dict["metadatas"], ids_list)
    middle_search_results = embedding_search(extract_collection, query, OPTION_COUNT)
    temp_client.delete_collection(name=client_name)
    
    """
    Below is the code for the old middle collection where we do not append the query
    """
    # probably want to be more clever with this name
    # client_name = str(uuid.uuid1())
    # extract_collection = temp_client.create_collection(name=client_name)
    # extract_collection.add(
    #     embeddings=extract_dict["embeddings"],
    #     documents=extract_dict["documents"],
    #     metadatas=extract_dict["metadatas"],
    #     ids=extract_dict["ids"],
    # )
    # middle_search_results = embedding_search(extract_collection, query, OPTION_COUNT)
    # temp_client.delete_collection(name=client_name)

    # Run the G part of RAG, log time
    results = get_generation(middle_search_results, query, option_count=OPTION_COUNT)
    end_time = time.time()
    logging.info(
        'Search query "'
        + str(query)
        + '" took '
        + str(end_time - start_time)
        + " seconds"
    )
    
    # Also add to database, and then return results
    timestamp = datetime.now().isoformat()
    add_query(query, end_time - start_time, timestamp)
    return results
