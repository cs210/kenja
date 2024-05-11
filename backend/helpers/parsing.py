import csv
import spacy
import pandas as pd
import time

nlp = spacy.load("en_core_web_sm")


def find_nouns(text: str):
    doc = nlp(text)
    nouns = []
    for token in doc:
        # Check if the token is a noun
        if token.pos_ == "NOUN":
            nouns.append(token.text)
    return nouns


def apply_nouns(series):
    all_nouns = []
    for _, value in series.items():
        val_str = str(value)
        nouns = find_nouns(val_str)
        all_nouns.extend(nouns)
    return all_nouns


def add_nouns(df):
    """
    Add nouns to dataframe
    """
    nouns_col = df.apply(lambda row: apply_nouns(row), axis=1)
    df["Nouns"] = nouns_col
    return df


# First, add the nouns column in
# df = pd.read_csv("supost_clean.csv")
# start_time = time.time()
# df = add_nouns(df)
# print("Time elapsed for creation: " + str(time.time() - start_time))
# df.to_csv("nouns_supost_clean.csv")
# nouns_col = df.apply(lambda row: apply_function(row), axis=1)
# df["Nouns"] = nouns_col

query = "I want something cool for my lawn"
start_time = time.time()
nouns = find_nouns(query)
print(nouns)
print("Time elapsed: " + str(time.time() - start_time) + "\n")

# Now, try searching against it
start_time = time.time()
df = pd.read_csv("nouns_supost_clean.csv")
search_string = "shirt"
result_series = df["Nouns"].apply(lambda x: search_string in x)
result_rows = df[result_series]
print("Time elapsed for search: " + str(time.time() - start_time))
print(result_rows)
