from venv import create
import torch
from tqdm import tqdm

# For chromadb with Chris's GPU
if torch.cuda.is_available():
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from generation_helpers import get_generation

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import uuid

# for RAG embedding model
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', model_max_length=8192)
model = AutoModel.from_pretrained('nomic-ai/nomic-embed-text-v1', trust_remote_code=True, rotary_scaling_factor=2)
model.eval()
if torch.cuda.is_available():
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
    encoded_input = tokenizer(texts_list, padding=True, truncation=True, return_tensors='pt')
    if torch.cuda.is_available():
        encoded_input = encoded_input.to("cuda")
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

def feature_to_collection_name(feature):
    """
    Chromadb collections can only have characters that are alphanumeric, -, or _
    so we use this function to easily access feature collections by converting 
    the names of features to an acceptable format.
    """
    collection_name = ""
    for i in range(len(feature)):
        if feature[i] == "/" or  feature[i] == "\'":
            collection_name += "-"
        elif not feature[i].isalnum() and feature[i] != "_" and feature[i] != "-":
            continue
        else:
            collection_name += feature[i]
    return collection_name

def create_collections(csv_list, id, features_list):
    """
    Create the collections for the first layer that corresponds to given features and 
    the middle collection. At the moment, the collections for the feature layer is created
    from all the supplied data.
    """
    # There should be at least 1 csv passed in to the function
    assert(len(csv_list) > 0)

    # If more than one csv file is given, all the csv files are outer joined in the supplied id
    # shared by all the csv files.
    if len(csv_list) > 1:
        main_dataframe = pd.merge(pd.read_csv(csv_list[0]), pd.read_csv(csv_list[1]), on=str(id), how="outer")
        for i in range(2, len(csv_list)):
            main_dataframe = pd.merge(main_dataframe, pd.read_csv(csv_list[i]), on=str(id), how="outer")
    else:
        main_dataframe = pd.read_csv(csv_list[0])

    # A helper function to populate a given collection with embeddings 
    def create_collection_embeddings(collection, documents, metadatas, ids):
        start_index = 0
        next_index = 5
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        desc = feature + " embedding creation progress"
        progress_bar = tqdm(total=len(documents), desc=desc)
        while (start_index < len(documents)):
            current_documents = documents[start_index:next_index]
            current_metadatas = metadatas[start_index:next_index]
            current_ids = ids[start_index:next_index]
            current_embeddings = open_source_create_embeddings(current_documents, True).tolist()
            add_to_collection(collection, current_embeddings, current_documents, current_metadatas, current_ids)
            if (next_index > len(documents)):
                progress_bar.update((len(documents) - start_index))
            else:
                progress_bar.update(5)
            start_index = next_index
            next_index += 5

    # A helper function to initialize the collection and relevant data 
    # needed to create embeddings
    def populate_collection(cur_df, main_df, collection_name, feature):
         # We want to reset these collections, so try to get collection if it exists and delete it
        chroma_client.get_or_create_collection(name=collection_name)
        chroma_client.delete_collection(name=collection_name)
        feature_collection = chroma_client.create_collection(name=collection_name)

        # Only use the columns for metadata that are the same for each row of the feature at hand and the id
        # (for example, if data corresponding to the same id have different timestamps but all have the same 
        # description, keep the description and get rid of the timestamp)
        drop_cols = [col for col in main_df.columns if col != feature and main_df[[id, col]].duplicated().sum() != main_df[id].duplicated().sum()]
        feature_metadatas = (main_df.drop(columns=drop_cols)).drop_duplicates().to_dict(orient="records")
        feature_documents = cur_df[feature].to_list()

        # Use a deterministic hash function on the id and feature to create ids
        feature_ids = list((cur_df.apply(lambda row: str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{row[id], row[feature]}")), axis=1)))
        create_collection_embeddings(feature_collection, feature_documents, feature_metadatas, feature_ids)
    
    # FIRST LEVEL COLLECTIONS
    for feature in features_list:
        collection_name = feature_to_collection_name(feature)        
        current_dataframe = main_dataframe[[id,feature]].drop_duplicates()
        populate_collection(current_dataframe, main_dataframe, collection_name, feature)
    
    # MIDDLE LEVEL COLLECTION

    # Create a dataframe that can be populated with the combined information for each id.
    num_ids = len(main_dataframe[id].unique())
    unique_ids = main_dataframe[id].unique()
    string_list = []
    for i in range(num_ids):
        string_list.append([unique_ids[i],""])
    middle_dataframe = pd.DataFrame(string_list, columns=[id, "combined_texts"])

    # Update the combined text for each id
    for feature in features_list:
        # Get number of unique entries for the feature
        unique_entries_series = main_dataframe.groupby(id)[feature].nunique()
        num_unique_entries = unique_entries_series.min()

        # Only keep The 3 longest entries of a feature -> can change this later
        if num_unique_entries > 3:
            num_unique_entries = 3
        main_dataframe["feature_length"] = main_dataframe[feature].apply(len)
        feature_df = main_dataframe.groupby(id).apply(lambda x: x.nlargest(num_unique_entries, "feature_length")).reset_index(drop=True)
        main_dataframe.drop("feature_length", axis=1, inplace=True)

        # Add the feature data to combined_texts
        feature_prefix =  feature + ": "
        feature_df[feature] = feature_prefix + feature_df[feature]
        feature_df = feature_df.groupby(id).agg({feature: lambda x: '\n\n'.join(map(str, x))}).reset_index()
        feature_df[feature] = feature_df[feature] + "\n\n"
        middle_dataframe["combined_texts"] = middle_dataframe["combined_texts"] + feature_df[feature]
    
    populate_collection(middle_dataframe, main_dataframe, "middle_collection", "combined_texts")


def find_match(query):
    """
    Call all functions.
    """
    descriptions_collection = chroma_client.get_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_collection(name="book_reviews")
    middle_collection = chroma_client.get_collection(name="middle_collection")

    # FIRST LEVEL
    review_search_results = embedding_search(reviews_collection, query, 20)
    titles_list = [dictionary["Title"] for dictionary in review_search_results["metadatas"][0]]
    titles_list = list(set(titles_list)) # there is a chance that the same book will appear multiple times
    description_search_results = embedding_search(descriptions_collection, query, 10)
    titles_list.extend(description_search_results["ids"][0])
    titles_list = list(set(titles_list)) # same book could have been given by both reviews and descriptions

    # SECOND LEVEL
    extract_dict = middle_collection.get(ids=titles_list, include=["embeddings", "documents", "metadatas"])
    # probably want to be more clever with this name
    client_name = str(uuid.uuid1())
    extract_collection = temp_client.create_collection(name=client_name)
    add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    middle_search_results = embedding_search(extract_collection, query, OPTION_COUNT)
    temp_client.delete_collection(name=client_name)

    return get_generation(middle_search_results, option_count=OPTION_COUNT)
