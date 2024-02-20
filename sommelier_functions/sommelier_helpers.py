import chromadb
from chromadb.config import Settings
import csv
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
chroma_client = chromadb.PersistentClient(path="./chromadb_data",
                                          settings=Settings(
                                              anonymized_telemetry=False))
client = OpenAI()

# Constants for data
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
    with open(DATA_PATH, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        # Create a wine info object
        for row in reader:
            all_wines.append(WineInfo(row))
    return all_wines[1:]


def create_embedding(description):
    """
    Given a description, return an embedding.
    """
    return client.embeddings.create(input=[description],
                                    model=EMBEDDING_MODEL).data[0].embedding


def add_wines(collection, wine):
    """
    Add wine to our vector database.
    """
    collection.add(
        embeddings=[create_embedding(wine.description)],
        documents=[wine.description],
        metadatas=[{"designation": wine.designation, "variety": wine.variety,
                    "winery": wine.winery, "country": wine.country,
                    "points": wine.points, "price": wine.price,
                    "province": wine.province, "region_1": wine.region_1,
                    "region_2": wine.region_2}],
        ids=[wine.id]
    )


def find_wine(collection, query):
    """
    Find a similar wine based on our query.
    """
    embedding = create_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )
    return results


def find_match(query):
    """
    Call all functions.
    """

    collection = chroma_client.get_or_create_collection(name="wines")

    if collection.count() == 0:
        print("populating data from file")
        # Initialize all data
        wines = load_data()
        for i in range(25):
            add_wines(collection, wines[i])
    else:
        print("Populating data from existing chromadb collection")

    print(collection)

    # Find a similar wine
    results = find_wine(collection, query)
    return results
