import chromadb
from chromadb.config import Settings
import pickle
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="../chromadb_data", settings=Settings(anonymized_telemetry=False)
)
client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
EMBEDDING_MODEL = "text-embedding-3-small"
DATASET_PATH = "./defined_datasets/5782_books_30_min_reviews_4.2_min_rating_50_min_review_length.pkl"


class BookInfo:
    """
    Class for book objects
    """

    def __init__(self, row):
        # books data csv data
        self.title = row[0]
        self.description = row[1]
        self.authors = row[2]
        self.book_cover_url = row[3]
        self.google_preview_link = row[4]
        self.publisher = row[5]
        self.publish_date = row[6]
        self.google_info_link = row[
            7
        ]  # Note: I am not sure how this is different from the google preview link
        self.category = row[8]
        # self.average_google_rating = row[9] I'm not actually sure what this value means, as it goes up to 4,900

        # Note: could also look at price later
        # books rating csv data
        self.id = None
        self.amazon_link = None
        self.amazon_average_book_score = (
            []
        )  # this starts as a list of all the review scores, and then we take the average at the end
        self.review_summaries = []
        self.reviews = []

def create_embedding(text):
    """
    Given a description, return an embedding.
    """
    return (
        client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        .data[0]
        .embedding
    )

def add_to_collection(collection, input, id, book):
    """
    Add an embedding to the appropriate vector database.
    """
    collection.add(
        embeddings=[create_embedding(input)],
        documents=[input],
        metadatas=[
            {
                "title": book.title,
                "description": book.description,
                "category": book.category,
                "score": book.amazon_average_book_score,
                "link": book.amazon_link,
                "publisher": book.publisher,
                "publication_date": book.publish_date,
                "length": len(input),
                "authors": book.authors
            }
        ],
        ids=[id],
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
    if update_collections:
        chroma_client.delete_collection(name="book_descriptions")
        chroma_client.delete_collection(name="book_reviews")
        descriptions_collection = chroma_client.create_collection(name="book_descriptions")
        reviews_collection = chroma_client.create_collection(name="book_reviews")

    if reviews_collection.count() == 0:
        print("populating data from file")
        with open(DATASET_PATH, "rb") as f:
            books = pickle.load(f)
            index = 0
            for book in books:
                if index == 500:
                    break
                print(index)
                for i in range(len(book.reviews)):
                    if i == 10:
                        break
                    current_id = f"{book.id,i}"
                    add_to_collection(reviews_collection, book.reviews[i], current_id, book)
                add_to_collection(descriptions_collection, book.description , book.id , book)
                index += 1
    else:
        print("Populating data from existing chromadb collection")
    print("here0!")
    review_search_results = embedding_search(reviews_collection, query, 200)
    print("here1!")
    description_search_results = embedding_search(descriptions_collection, query, 20)
    print("here2!")
    # return description_results