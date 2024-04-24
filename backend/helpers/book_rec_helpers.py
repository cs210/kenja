from venv import create

# For chromadb
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from generation_helpers import get_generation

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import uuid

# for RAG embedding model
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', model_max_length=8192)
model = AutoModel.from_pretrained('nomic-ai/nomic-embed-text-v1', trust_remote_code=True, rotary_scaling_factor=2)
model.eval()
model.to("cuda")

OPTION_COUNT = 5

load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="./chromadb_data", settings=Settings(anonymized_telemetry=False)
)
temp_client = chromadb.PersistentClient(
    path="./chromadb_data", settings=Settings(anonymized_telemetry=False)
)


def open_source_create_embeddings(texts_list, is_document):
    """
    Use the new local embeddings model to handle embeddings.
    """
    # Embed based on a document or a query
    if is_document:
        texts_list = ["search_document: " + item for item in texts_list]
    else:
        texts_list = ["search_query: " +  item for item in texts_list]
    
    # Mean pooling function to help with embeddings
    def mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    # Encode input and run through the model
    encoded_input = tokenizer(texts_list, padding=True, truncation=True, return_tensors='pt').to("cuda")
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Return the embeddings
    embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings


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
    embedding = open_source_create_embeddings([query], False).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n_results)
    return results

def process_data(books_path, reviews_path, min_num_reviews, min_rating, min_review_length, min_description_length):
    """
    Load data from the original Kaggle dataset.
    """
    books_df = pd.read_csv(books_path)
    books_df = books_df.dropna(subset=['description', 'categories'])
    books_df = books_df[books_df['description'].str.len() >= min_description_length]

    reviews_df = pd.read_csv(reviews_path)
    reviews_df = reviews_df.dropna(subset=['review/text'])

    # remove any duplicate reviews
    reviews_df = reviews_df.drop_duplicates(subset=["review/text"])

    # only keep books that haven't already been filtered out
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # give the review an id using deterministic hash function
    reviews_df['reviewId'] = reviews_df.apply(lambda row: str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{row['Title'], row['review/text']}")), axis=1)

    # drop any books that don't have the specified minimum average rating
    average_rating_df = reviews_df.groupby('Title')['review/score'].mean().reset_index()
    average_rating_df = average_rating_df[average_rating_df["review/score"] >= min_rating]
    average_rating_df = average_rating_df.rename(columns = {"review/score": "average_rating"})
    books_df = pd.merge(average_rating_df, books_df, on="Title", how="inner")
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # only keep reviews that are long enough
    reviews_df = reviews_df[reviews_df["review/text"].str.len() >= min_review_length]

    # only want reviews that give a score of at least 4
    reviews_df = reviews_df[reviews_df["review/score"] >= 4]

    # want at least num_reviews for a book
    title_counts = reviews_df["Title"].value_counts()
    title_counts = title_counts[title_counts >= min_num_reviews]
    enough_reviews_df = pd.DataFrame({"Title":title_counts.index})
    reviews_df = reviews_df[reviews_df['Title'].isin(enough_reviews_df['Title'])]

    # add the review length as an entry
    reviews_df["review_length"] = reviews_df["review/text"].apply(lambda x: len(str(x)))

    # update books df for any titles removed from reviews df
    books_df = books_df[books_df['Title'].isin(reviews_df['Title'])]

    # add the description length as an entry
    books_df["description_length"] = books_df["description"].apply(lambda x: len(str(x)))

    return books_df, reviews_df

def create_collections(books_path, reviews_path):
    def create_collection_embeddings(collection, documents, metadatas, ids):
        start_index = 0
        next_index = 5
        torch.cuda.empty_cache()
        while (start_index < len(documents)):
            print(start_index)
            current_documents = documents[start_index:next_index]
            current_metadatas = metadatas[start_index:next_index]
            current_ids = ids[start_index:next_index]
            current_embeddings = open_source_create_embeddings(current_documents, True).tolist()
            add_to_collection(collection, current_embeddings, current_documents, current_metadatas, current_ids)
            start_index = next_index
            next_index += 5
        
    """
    Create the embeddings for vector database search.
    """
    # We want to reset these collections, so try to get collection if it exists and delete it
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")
    descriptions_collection = chroma_client.delete_collection(name="book_descriptions")
    reviews_collection = chroma_client.delete_collection(name="book_reviews")
    middle_collection = chroma_client.delete_collection(name="middle_collection")
    
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")

    # Process and clean up data
    books_df, reviews_df = process_data(books_path, reviews_path, 30, 4.2, 50, 20)
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]
    reviews_df["helpful_votes"] = reviews_df["review/helpfulness"].apply(lambda x: str(x)[:x.find("/")])
    reviews_df["helpful_votes"] = pd.to_numeric(reviews_df["helpful_votes"])
    # Only take the top 10 reviews for each book based on the number of helpful upvotes for now
    top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(10, "helpful_votes")).reset_index(drop=True)

    # FIRST LEVEL COLLECTIONS
    books_documents = books_df["description"].tolist()
    books_metadatas = books_df.to_dict(orient="records")
    books_ids = books_df["Title"].tolist()
    create_collection_embeddings(descriptions_collection, books_documents, books_metadatas, books_ids)
    
    top_reviews_documents = top_reviews_df["review/text"].tolist()
    top_reviews_metadatas = top_reviews_df.to_dict(orient="records")
    top_reviews_ids = top_reviews_df["reviewId"].tolist()
    create_collection_embeddings(reviews_collection, top_reviews_documents, top_reviews_metadatas, top_reviews_ids)

    # Clean up data for second level
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

    # SECOND LEVEL COLLECTIONS
    middle_documents = middle_df["combined_text"].tolist()
    middle_metadatas = middle_df.to_dict(orient="records")
    middle_ids = middle_df["Title"].tolist()
    create_collection_embeddings(middle_collection, middle_documents, middle_metadatas, middle_ids)

# Contains names of relavent collections
class ProductDescription:
    #User specified features 
    feature_collections: list[str]
    hidden_collections: list[str]
    middle_collection: str

def find_match(query, product_description: ProductDescription):
    """
    Call all functions.
    """
    feature_collections = []
    for collection in product_description.feature_collections:
        feature_collections.append(chroma_client.get_collection(name=collection))
    for collection in product_description.hidden_collections:
        feature_collections.append(chroma_client.get_collection(name=collection))
    
    middle_collection = chroma_client.get_collection(name=product_description.middle_collection)

    # FIRST LEVEL
    titles_list = []
    for feature_collection in feature_collections:
        partial_search_results = embedding_search(feature_collection, query, max(20, .05 * feature_collection.count()))
        partial_titles_list = [dictionary["ids"] for dictionary in partial_search_results["metadatas"][0]]
        partial_titles_list = list(set(partial_titles_list)) # there is a chance that the same book will appear multiple times
        titles_list.extend(partial_titles_list)
        titles_list = list(set(titles_list))
        
    # SECOND LEVEL
    extract_dict = middle_collection.get(ids=titles_list, include=["embeddings", "documents", "metadatas"])
    # probably want to be more clever with this name
    client_name = str(uuid.uuid1())
    extract_collection = temp_client.create_collection(name=client_name)
    add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    middle_search_results = embedding_search(extract_collection, query, OPTION_COUNT)
    temp_client.delete_collection(name=client_name)

    return get_generation(middle_search_results, option_count=OPTION_COUNT)
