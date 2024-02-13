import chromadb
from chromadb.config import Settings
chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))

collection = chroma_client.create_collection(name="test")

collection.add(
    embeddings=[[1.2, 2.3, 4.5], [6.7, 8.2, 9.2]],
    documents=["This is a document", "This is another document"],
    metadatas=[{"source": "my_source"}, {"source": "my_source"}],
    ids=["id1", "id2"]
)

results = collection.query(
    query_embeddings=[[1.2, 2.3, 4.5]],
    n_results=2
)

print(results)