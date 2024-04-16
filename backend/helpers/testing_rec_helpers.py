from book_rec_helpers import *
import pandas as pd
BOOKS_DATASET_PATH = "./defined_datasets/books_df_4494_books_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"
REVIEWS_DATASET_PATH = "./defined_datasets/reviews_df_448893_total_reviews_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"

#create_collections(BOOKS_DATASET_PATH, REVIEWS_DATASET_PATH)
# create_collections()
results = find_match("Harry Potter.", False)
for result in results:
    print()
    print(result)
    print()