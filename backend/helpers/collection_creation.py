from .embedding_creation import create_collection_embeddings
from .add_nouns import add_nouns

import torch

# For chromadb with Chris's GPU
if torch.cuda.is_available():
    __import__("pysqlite3")
    import sys

    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

import chromadb
from chromadb.config import Settings
import pandas as pd
import uuid

EMBEDDINGS_PATH = "./embeddings/"



def feature_to_collection_name(feature):
    """
    Chromadb collections can only have characters that are alphanumeric, -, or _
    so we use this function to easily access feature collections by converting
    the names of features to an acceptable format.
    """
    collection_name = ""
    for i in range(len(feature)):
        if feature[i] == "/" or feature[i] == "'":
            collection_name += "-"
        elif not feature[i].isalnum() and feature[i] != "_" and feature[i] != "-":
            continue
        else:
            collection_name += feature[i]
    return collection_name


# A helper function to initialize the collection and relevant data
# needed to create embeddings
def populate_collection(cur_df, main_df, id, collection_name, feature, is_middle, chroma_client):
    # We want to reset these collections, so try to get collection if it exists and delete it
    chroma_client.get_or_create_collection(name=collection_name)
    chroma_client.delete_collection(name=collection_name)
    feature_collection = chroma_client.create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    # Only use the columns for metadata that are the same for each row of the feature at hand and the id
    # (for example, if data corresponding to the same id have different timestamps but all have the same
    # description, keep the description and get rid of the timestamp)
    drop_cols = [
        col
        for col in main_df.columns
        if col != feature
        and main_df[[id, col]].duplicated().sum() != main_df[id].duplicated().sum()
    ]
    feature_metadatas = (
        main_df.drop(columns=drop_cols)
    ).drop_duplicates()  # we make this a dict later now
    feature_documents = cur_df[feature].to_list()
    if is_middle:
        feature_ids = list(
            (
                cur_df.apply(
                    lambda row: str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{row[id]}")),
                    axis=1,
                )
            )
        )
    else:
        feature_metadatas["VALUE_ID"] = cur_df[id]
        # Use a deterministic hash function on the id and feature to create ids
        feature_ids = list(
            (
                cur_df.apply(
                    lambda row: str(
                        uuid.uuid3(uuid.NAMESPACE_DNS, f"{row[id], row['Nouns']}") # make this nouns as hacky solution to extraction subclasses later
                    ),
                    axis=1,
                )
            )
        )
    feature_metadatas = feature_metadatas.to_dict(orient="records")
    create_collection_embeddings(
        feature_collection,
        feature,
        feature_documents,
        feature_metadatas,
        feature_ids,
    )


def create_collections(csv_list, id, features_list, file_id, encoding):
    """
    Create the collections for the first layer that corresponds to given features and
    the middle collection. At the moment, the collections for the feature layer is created
    from all the supplied data.
    """
    # There should be at least 1 csv passed in to the function
    assert len(csv_list) > 0

    # Create chroma and temp clients for specific file
    chroma_client = chromadb.PersistentClient(
        path=EMBEDDINGS_PATH + file_id, settings=Settings(anonymized_telemetry=False)
    )

    # If more than one csv file is given, all the csv files are outer joined in the supplied id
    # shared by all the csv files.
    if len(csv_list) > 1:
        main_dataframe = pd.merge(
            pd.read_csv(csv_list[0], encoding=encoding),
            pd.read_csv(csv_list[1], encoding=encoding),
            on=str(id),
            how="outer",
        )
        for i in range(2, len(csv_list)):
            main_dataframe = pd.merge(
                main_dataframe,
                pd.read_csv(csv_list[i], encoding=encoding),
                on=str(id),
                how="outer",
            )
    else:
        main_dataframe = pd.read_csv(csv_list[0], encoding=encoding)

    # Add a nouns column to the dataframe
    main_dataframe = add_nouns(main_dataframe)
    main_dataframe = main_dataframe.reset_index(drop=True)

    # NOUN COLLECTION
    collection_name = feature_to_collection_name("Nouns")
    current_dataframe = main_dataframe[[id, "Nouns"]].drop_duplicates()
    populate_collection(
        current_dataframe, main_dataframe, id, collection_name, "Nouns", False, chroma_client
    )


    # FIRST LEVEL COLLECTIONS
    for feature in features_list:
        collection_name = feature_to_collection_name(feature)
        if feature != id:
            current_dataframe = main_dataframe[[id, feature, "Nouns"]].drop_duplicates()
        else:
            current_dataframe = main_dataframe[[id]].drop_duplicates()
        populate_collection(
            current_dataframe, main_dataframe, id, collection_name, feature, False, chroma_client
        )
    # MIDDLE LEVEL COLLECTION

    # Create a dataframe that can be populated with the combined information for each id.
    num_ids = len(main_dataframe[id].unique())
    unique_ids = main_dataframe[id].unique()
    string_list = []
    for i in range(num_ids):
        string_list.append([unique_ids[i], ""])
    middle_dataframe = pd.DataFrame(string_list, columns=[id, "combined_texts"])
    middle_dataframe = middle_dataframe.sort_values(by=id)

    # # Update the combined text for each id
    for feature in features_list:
        if feature != id:
            # Get number of unique entries for the feature
            unique_entries_series = main_dataframe.groupby(id)[feature].nunique()
            num_unique_entries = unique_entries_series.min()

            # Only keep The 3 longest entries of a feature -> can change this later
            if num_unique_entries > 3:
                num_unique_entries = 3
            main_dataframe["feature_length"] = main_dataframe[feature].apply(len)
            feature_df = (
                main_dataframe.groupby(id)
                .apply(lambda x: x.nlargest(num_unique_entries, "feature_length"))
                .reset_index(drop=True)
            )
            main_dataframe.drop("feature_length", axis=1, inplace=True)
        else:
            feature_df = main_dataframe[[id]].drop_duplicates().reset_index(drop=True)

        # Add the feature data to combined_texts
        feature_prefix = feature + ": "
        feature_df.loc[:, feature] = feature_prefix + feature_df[feature]
        if feature != id:
            feature_df = (
                feature_df.groupby(id)
                .agg({feature: lambda x: "\n\n".join(map(str, x))})
                .reset_index()
            )
        feature_df.loc[:, feature] = feature_df[feature] + "\n\n"
        feature_df = feature_df.sort_values(by=id)
        middle_dataframe.loc[:, "combined_texts"] = (
            middle_dataframe.loc[:, "combined_texts"] + feature_df.loc[:, feature]
        ).reset_index(drop=True)
        middle_dataframe = middle_dataframe.reset_index(drop=True)
    
    # Do the below to make sure that values will line up
    main_dataframe = main_dataframe.sort_values(by=id)
    main_dataframe = main_dataframe.reset_index(drop=True)
    populate_collection(
        middle_dataframe, main_dataframe, id, "middle_collection", "combined_texts", True, chroma_client
    )