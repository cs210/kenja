from venv import create
import chromadb
from chromadb.config import Settings
import pickle
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd

load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="../chromadb_data", settings=Settings(anonymized_telemetry=False)
)
client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
EMBEDDING_MODEL = "text-embedding-3-small"
BOOKS_DATASET_PATH = "./defined_datasets/books_df_5776_books_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"
REVIEWS_DATASET_PATH = "./defined_datasets/reviews_df_633987_total_reviews_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"

def create_embedding(text):
    """
    Given a description, return an embedding.
    """
    return (
        client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        .data[0]
        .embedding
    )

def add_to_collection(collection, embeddings, documents, metadatas, ids):
    """
    Add an embedding to the appropriate vector database.
    """
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

def embedding_search(collection, query, n_results):
    embedding = create_embedding(query)
    results = collection.query(query_embeddings=embedding, n_results=n_results)
    return results


def find_match(query, update_collections = False):
    """
    Call all functions.
    """
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")
    if update_collections:
        chroma_client.delete_collection(name="book_descriptions")
        chroma_client.delete_collection(name="book_reviews")
        chroma_client.delete_collection(name="middle_collection")
        descriptions_collection = chroma_client.create_collection(name="book_descriptions")
        reviews_collection = chroma_client.create_collection(name="book_reviews")
        middle_collection = chroma_client.create_collection(name="middle_collection")

    if reviews_collection.count() == 0:
        print("populating data from file")

        # FIRST LEVEL
        books_df = pd.read_csv(BOOKS_DATASET_PATH, nrows=5)

        reviews_df = pd.read_csv(REVIEWS_DATASET_PATH)
        reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

        reviews_df["helpful_votes"] = reviews_df["review/helpfulness"].apply(lambda x: str(x)[:x.find("/")])
        reviews_df["helpful_votes"] = pd.to_numeric(reviews_df["helpful_votes"])

        # only take the top 10 reviews for each book based on the number of helpful upvotes for now
        top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(10, "helpful_votes")).reset_index(drop=True)

        books_metadatas = books_df.to_dict(orient="records")
        reviews_metadatas = top_reviews_df.to_dict(orient="records")
        
        books_df["description_embedding"] = books_df["description"].apply(lambda x: create_embedding(x))
        top_reviews_df["review_embedding"] = top_reviews_df["review/text"].apply(lambda x: create_embedding(x))

        books_embeddings = books_df["description_embedding"].tolist()
        reviews_embeddings = top_reviews_df["review_embedding"].tolist()

        books_ids = books_df["Title"].tolist()
        reviews_ids = top_reviews_df["reviewId"].tolist()

        books_documents = books_df["description"].tolist()
        reviews_documents = top_reviews_df["review/text"].to_list()

        add_to_collection(reviews_collection, reviews_embeddings, reviews_documents, reviews_metadatas, reviews_ids)
        add_to_collection(descriptions_collection, books_embeddings, books_documents, books_metadatas, books_ids)

        # SECOND LEVEL
        exclude = ["description_embedding", "description_length"]
        middle_df = books_df[[col for col in books_df.columns if col not in exclude]]
        middle_df["description"] = "Description: " + middle_df["description"] + "\n\n"

        top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(4, "helpful_votes")).reset_index(drop=True)

        top_reviews_df = top_reviews_df[["Title", "review/text"]]
        top_reviews_df["review/text"] = "Review: " + top_reviews_df["review/text"]
        top_reviews_df = top_reviews_df.groupby("Title").agg({'review/text': lambda x: '\n\n'.join(map(str, x))}).reset_index()

        middle_df = pd.merge(middle_df, top_reviews_df, on="Title", how="inner")
        
        middle_df["combined_text"] = middle_df["description"] + middle_df["review/text"]
        middle_df = middle_df.drop("description", axis=1)
        middle_df = middle_df.drop("review/text", axis=1)
        middle_df["text_length"] = middle_df["combined_text"].apply(lambda x: len(str(x)))

        middle_metadatas = middle_df.to_dict(orient="records")
        middle_df["combined_text_embedding"] = middle_df["combined_text"].apply(lambda x: create_embedding(x))
        middle_embeddings = middle_df["combined_text_embedding"].tolist()
        middle_ids = middle_df["Title"].tolist()
        middle_documents = middle_df["combined_text"].to_list()
        add_to_collection(middle_collection, middle_embeddings, middle_documents, middle_metadatas, middle_ids)
    else:
        print("Populating data from existing chromadb collection")
    review_search_results = embedding_search(reviews_collection, query, 2)
    titles_list = [dictionary["Title"] for dictionary in review_search_results["metadatas"][0]]
    titles_list = list(set(titles_list)) # there is a chance that the same book will appear multiple times
    description_search_results = embedding_search(descriptions_collection, query, 2)
    titles_list.extend(description_search_results["ids"][0])
    titles_list = list(set(titles_list)) # same book could have been given by both reviews and descriptions

    # SECOND LEVEL
    extract_dict = middle_collection.get(ids=titles_list, include=["embeddings", "documents", "metadatas"])
    # probably want to be more clever with this name
    extract_collection = chroma_client.create_collection(name=query)
    add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    middle_search_results = embedding_search(extract_collection, query, 1)
    chroma_client.delete_collection(name=query)
    print(middle_search_results)