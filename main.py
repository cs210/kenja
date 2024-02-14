"""
Simple recommendation algorithm + frontend for wine.
"""
import chromadb
from chromadb.config import Settings
import csv
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st

# Set up OpenAI and Chroma client
load_dotenv()
client = OpenAI()
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

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
        embeddings=[create_embedding(wine.description)],
        documents=[wine.description],
        metadatas=[{"designation": wine.designation, "variety": wine.variety, "winery": wine.winery}],
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
    # Initialize all data
    wines = load_data()
    collection = chroma_client.create_collection(name="wines")
    for i in range(25):
        add_wines(collection, wines[i])

    # Find a similar wine
    results = find_wine(collection, query)
    return results

# Header
st.title("🍷 Sommelier")
st.subheader("You give us a request, we give you wine recs.")

# Core form/search function
submitted = False
slider_val = ""
with st.form("input_form"):
   st.write("Describe what wine you're looking for...")
   slider_val = st.text_input("Ex: \"I want a wine that goes well with gouda and has notes of paprika.\"")

   # Submit function
   submitted = st.form_submit_button("Submit")

# Checking for submitted
if submitted:
    st.subheader("Recommendations")
    results = find_match(slider_val)

    # Display results
    for i in range(len(results['documents'][0])):
        metadata = results['metadatas'][0][i]
        st.write("🍷 " + metadata['designation'])
        st.write("Vineyard: " + metadata['winery'])
        st.write("Variety: " + metadata['variety'])
        st.divider()
    