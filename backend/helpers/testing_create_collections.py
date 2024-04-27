from f_and_f_helpers import *
import pandas as pd

# For single, merged dataset dataset 
create_collections(["./books_information/mini_books_datasets/mini_books_rating.csv", "./books_information/mini_books_datasets/mini_books_data.csv"], "Title", ["description", "review/text"])
# For multiple, unmerged datasets
# create_collections(["./books_information/books_datasets/structured_book_dataset.csv"], "Title", ["description", "review/text"])