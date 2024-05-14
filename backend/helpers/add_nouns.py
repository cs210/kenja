"""
Sample code for noun parsing!
"""
import torch
if torch.cuda.is_available():
    __import__("pysqlite3")
    import sys
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
import chromadb
from chromadb.config import Settings

import spacy
import pandas as pd
import uuid
import time
from tqdm import tqdm


nlp = spacy.load("en_core_web_sm")


def find_nouns(text: str):
    """
    Given a certain string, find all the nouns in the string
    """
    doc = nlp(text)
    nouns = []
    for token in doc:
        if token.pos_ == "NOUN":
            nouns.append(token.text)
    return nouns


def apply_nouns(series):
    """
    Across a row of a CSV file, find all the nouns across all column contents!
    """
    all_nouns = []
    for _, value in series.items():
        val_str = str(value)
        nouns = find_nouns(val_str)
        all_nouns.extend(nouns)
    return " ".join(all_nouns)


def add_nouns(df):
    """
    Add nouns to dataframe
    """
    tqdm.pandas(desc="Adding Nouns")
    nouns_col = df.progress_apply(lambda row: apply_nouns(row), axis=1)
    df["Nouns"] = nouns_col
    return df