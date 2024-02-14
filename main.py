"""
Simple recommendation algorithm + frontend for wine.
"""
import chromadb
from chromadb.config import Settings
import csv
from dotenv import load_dotenv
from openai import OpenAI

""" Set up OpenAI and Chroma client """
load_dotenv()
client = OpenAI()
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

""" Constants for data """
CONFIG_FILE = "config.json"
DATA_PATH = "data/initial_wine_data.csv"
EMBEDDING_MODEL = "text-embedding-3-small"

class WineInfo:
    """
    Class for wine objects
    """
    def __init__(self, row):
        self.raw_content = row
        self.id = row[0]
        self.country = row[1]
        self.description = row[2]
        self.designation = row[3]
        self.points = row[4]
        self.price = row[5]
        self.province = row[6]
        self.region_1 = row[7]
        self.region_2 = row[8]
        self.variety = row[9]
        self.winery = row[10]

def load_data():
    """
    Load data: currently in CSV file.
    """
    # Open the CSV file
    all_wines = []
    with open(DATA_PATH, mode='r') as file:
        reader = csv.reader(file)
        
        # Create a wine info object
        for row in reader:
            all_wines.append(WineInfo(row))
    return all_wines[1:]

def create_embedding(description):
    """
    Given a description, return an embedding.
    """
    return client.embeddings.create(input = [description], model=EMBEDDING_MODEL).data[0].embedding

def add_wines(collection, wine):
    """
    Add wine to our vector database.
    """
    collection.add(
        embeddings=[[1, 2, 3]],#create_embedding(wine.description)],
        documents=[wine.description],
        metadatas=[{"price": wine.price}],
        ids=[wine.id]
    )

def find_wine(query):
    """
    Find a similar wine based on our query.
    """
    embedding = create_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )
    return results

if __name__ == "__main__":
    """
    Call all functions.
    """
    # Load data
    wines = load_data()

    # Create collection
    collection = chroma_client.create_collection(name="wines")

    # Add wines to collection
    for i in range(30):
        add_wines(collection, wines[i])
    