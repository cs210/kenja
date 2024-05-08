from faf_helpers import *

# create_collections(["./books_information/mini_books_datasets/mini_books_rating.csv", "./books_information/mini_books_datasets/mini_books_data.csv"], "Title", ["description","review/text"], "testing")

collections = find_chroma_collections("testing")
features = []
for col in collections:
    if (col.name != "middle_collection" and col.name != "hidden_collection"):
        features.append(col.name)

# Form description and call find match
description = ProductDescription(
    feature_collections=features,
    hidden_collections="hidden_collection",
    middle_collection="middle_collection"
)
results = find_match("testing functionality", description, "testing")