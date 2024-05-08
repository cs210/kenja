from venv import create
import torch
from tqdm import tqdm

# For chromadb with Chris's GPU
if torch.cuda.is_available():
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

from .generation_helpers import get_generation

import chromadb
from chromadb.config import Settings
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import uuid
from typing import List

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
EMBEDDINGS_PATH = "./embeddings/"
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

def create_collections(csv_list, id, features_list, file_id):
    """
    Create the collections for the first layer that corresponds to given features and 
    the middle collection. At the moment, the collections for the feature layer is created
    from all the supplied data.
    """
    # There should be at least 1 csv passed in to the function
    assert(len(csv_list) > 0)
    
    # Create chroma and temp clients for specific file
    chroma_client = chromadb.PersistentClient(
    path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )
    temp_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )

    # If more than one csv file is given, all the csv files are outer joined in the supplied id
    # shared by all the csv files.
    if len(csv_list) > 1:
        main_dataframe = pd.merge(pd.read_csv(csv_list[0]), pd.read_csv(csv_list[1]), on=str(id), how="outer")
        for i in range(2, len(csv_list)):
            main_dataframe = pd.merge(main_dataframe, pd.read_csv(csv_list[i]), on=str(id), how="outer")
    else:
        main_dataframe = pd.read_csv(csv_list[0])
    
    # put the id information into a column named VALUE_ID so that extracting proper information during 
    # find_match can be done more easily (don't have to remember what id was)
    main_dataframe["VALUE_ID"] = main_dataframe[id]

    # A helper function to populate a given collection with embeddings 
    def create_collection_embeddings(collection, feature, documents, metadatas, ids):
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
        feature_metadatas = (main_df.drop(columns=drop_cols))
        if len(feature_metadatas) != len(cur_df):
            feature_metadatas = feature_metadatas.drop_duplicates()
        assert(len(feature_metadatas) == len(cur_df))
        feature_metadatas = feature_metadatas.to_dict(orient="records")
        feature_documents = cur_df[feature].to_list()
        feature_ids = list((cur_df.apply(lambda row: str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{row[id], row[feature]}")), axis=1)))
        create_collection_embeddings(feature_collection, feature, feature_documents, feature_metadatas, feature_ids)
    

    # # FIRST LEVEL COLLECTIONS
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
        feature_df[feature] = feature_prefix + feature_df[feature].astype(str)
        feature_df = feature_df.groupby(id).agg({feature: lambda x: '\n\n'.join(map(str, x))}).reset_index()
        feature_df[feature] = feature_df[feature] + "\n\n"
        middle_dataframe["combined_texts"] = middle_dataframe["combined_texts"] + feature_df[feature]
    populate_collection(middle_dataframe, main_dataframe, "middle_collection", "combined_texts")

    # HIDDEN LEVEL COLLECTION
    # for every row in the merged dataframe of the given csv files, take all columns that aren't a
    # part of the features and embed them to create the hidden collection
    string_list = []
    for cur_id in main_dataframe[id]:
        string_list.append([cur_id,""])
    hidden_dataframe = pd.DataFrame(string_list, columns=[id, "hidden_texts"])

    hidden_columns = [col for col in main_dataframe.columns if col not in features_list]
    # Update the combined text for each id
    for hidden_col in hidden_columns:
        if hidden_col == id or hidden_col == "VALUE_ID":
            continue
        feature_prefix = hidden_col + ": "
        hidden_dataframe.loc[:, "hidden_texts"] = hidden_dataframe["hidden_texts"] + feature_prefix + main_dataframe[hidden_col].astype(str) + "\n\n"
    populate_collection(hidden_dataframe, main_dataframe, "hidden_collection", "hidden_texts")

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
    def __init__(self, feature_collections: List[str], hidden_collections: List[str], middle_collection: str):
        self.feature_collections = feature_collections
        self.hidden_collections = hidden_collections
        self.middle_collection = middle_collection

def find_match(query, product_description: ProductDescription, file_id):
    """
    Call all functions.
    """
    # Create chroma and temp clients for specific file
    chroma_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )
    temp_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )

    # Get all feature collections
    feature_collections = []
    for collection in product_description.feature_collections:
        feature_collections.append(chroma_client.get_collection(name=collection))
    # for collection in product_description.hidden_collections:
    #     feature_collections.append(chroma_client.get_collection(name=collection))
    
    middle_collection = chroma_client.get_collection(name=product_description.middle_collection)

    hidden_collection = chroma_client.get_collection(name=product_description.hidden_collections)

    # FIRST LEVEL
    results_list = []
    for feature_collection in feature_collections:
        partial_search_results = embedding_search(feature_collection, query, max(20, int(.05 * feature_collection.count())))
        # Set up list to extract from next collection using metadatas
        # See https://github.com/chroma-core/chroma/blob/main/examples/basic_functionality/where_filtering.ipynb
        for dictionary in partial_search_results["metadatas"][0]:
            if dictionary['VALUE_ID'] not in results_list:
                results_list.append(dictionary['VALUE_ID'])
    
    # HIDDEN LEVEL
    # probably want to be more clever with this name
    client_name = str(uuid.uuid1())
    extract_collection = temp_client.create_collection(name=client_name)
    hidden_ids = results_list


    # client_name = str(uuid.uuid1())
    # extract_collection = temp_client.create_collection(name=client_name)
    # print("here1!")
    # for value_dict in results_list:
    #     extract_dict = hidden_collection.get(where=value_dict, include=["embeddings", "documents", "metadatas"])
    #     add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    # print("here2!")
    # hidden_search_results = embedding_search(extract_collection, query, 10)
    # temp_client.delete_collection(name=client_name)

    results_list = []
    for dictionary in hidden_search_results["metadatas"][0]:
        if {"VALUE_ID": dictionary['VALUE_ID']} not in results_list:
            results_list.append({"VALUE_ID": dictionary['VALUE_ID']})

    
    # SECOND LEVEL
    # probably want to be more clever with this name
    client_name = str(uuid.uuid1())
    extract_collection = temp_client.create_collection(name=client_name)
    for value_dict in results_list:
        extract_dict = hidden_collection.get(where=value_dict, include=["embeddings", "documents", "metadatas"])
        add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    middle_search_results = embedding_search(extract_collection, query, OPTION_COUNT)
    temp_client.delete_collection(name=client_name)

    # Run the G part of RAG
    return get_generation(middle_search_results, option_count=OPTION_COUNT)