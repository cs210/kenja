from book_rec_helpers import BookInfo
import csv
import os
import pickle
import pandas as pd
import uuid

BOOKS_DATA_PATH = "archive/books_data.csv"
BOOKS_RATING_PATH = "archive/books_rating.csv"

def load_kaggle_data(min_num_reviews, min_rating, min_review_length, min_description_length):
    """
    Load data from the original Kaggle dataset.
    """
    books_df = pd.read_csv(BOOKS_DATA_PATH)
    books_df = books_df.dropna(subset=['description', 'categories'])
    books_df = books_df[books_df['description'].str.len() >= min_description_length]

    reviews_df = pd.read_csv(BOOKS_RATING_PATH)
    reviews_df = reviews_df.dropna(subset=['review/text'])

    # only keep books that haven't already been filtered out
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # give the review an id using deterministic hash function
    reviews_df['reviewId'] = reviews_df.apply(lambda row: uuid.uuid3(uuid.NAMESPACE_DNS, f"{row['Title'], row['review/text']}"), axis=1)

    # drop any books that don't have the specified minimum average rating
    average_rating_df = reviews_df.groupby('Title')['review/score'].mean().reset_index()
    average_rating_df = average_rating_df[average_rating_df["review/score"] >= min_rating]
    average_rating_df = average_rating_df.rename(columns = {"review/score": "average_rating"})
    books_df = pd.merge(average_rating_df, books_df, on="Title", how="inner")
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # only keep reviews that are long enough
    reviews_df = reviews_df[reviews_df["review/text"].str.len() >= min_review_length]

    # only want reviews that give a score of at least 4
    reviews_df = reviews_df[reviews_df["review/score"] >= 4]

    # want at least num_reviews for a book
    title_counts = reviews_df["Title"].value_counts()
    title_counts = title_counts[title_counts >= min_num_reviews]
    enough_reviews_df = pd.DataFrame({"Title":title_counts.index})
    reviews_df = reviews_df[reviews_df['Title'].isin(enough_reviews_df['Title'])]

    # add the review length as an entry
    reviews_df["review_length"] = reviews_df["review/text"].apply(lambda x: len(str(x)))

    # update books df for any titles removed from reviews df
    books_df = books_df[books_df['Title'].isin(reviews_df['Title'])]

    # add the description length as an entry
    books_df["description_length"] = books_df["description"].apply(lambda x: len(str(x)))

    return books_df, reviews_df

def create_new_subset(min_num_reviews, min_rating, min_review_length, min_description_length):
    folder_path = "./defined_datasets"
    if not os.path.exists(folder_path):
        # Create the folder
        os.makedirs(folder_path)

    books_df, reviews_df = load_kaggle_data(float(min_num_reviews), float(min_rating), float(min_review_length), float(min_description_length))

    num_books = books_df["Title"].nunique()
    total_num_reviews = reviews_df["reviewId"].nunique()
    books_file_name = "books_df_" + str(num_books) + "_books_" + str(min_num_reviews) + "_min_num_reviews_" + str(min_rating) + "_min_rating_" + str(min_description_length) + "_min_description_length_" + str(min_review_length) + "_min_review_length.csv"
    books_file_path = "./defined_datasets/" + books_file_name
    reviews_file_name = "reviews_df_" + str(total_num_reviews) + "_total_reviews_" + str(min_num_reviews) + "_min_num_reviews_" + str(min_rating) + "_min_rating_" + str(min_description_length) + "_min_description_length_" + str(min_review_length) + "_min_review_length.csv"
    reviews_file_path = "./defined_datasets/" + reviews_file_name
    books_df.to_csv(books_file_path, index = False)
    reviews_df.to_csv(reviews_file_path, index = False)

if __name__ == "__main__":
    min_num_reviews = 30
    min_rating = 4.2
    min_review_length = 50
    min_description_length = 20
    create_new_subset(min_num_reviews, min_rating, min_review_length, min_description_length)
