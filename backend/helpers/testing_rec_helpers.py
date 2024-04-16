from book_rec_helpers import *
import pandas as pd
BOOKS_DATASET_PATH = "./archive/books_data.csv"
REVIEWS_DATASET_PATH = "./archive/books_rating.csv"

#create_collections(BOOKS_DATASET_PATH, REVIEWS_DATASET_PATH)
results = find_match("Harry Potter.", False)
for result in results:
    print()
    print(result)
    print()