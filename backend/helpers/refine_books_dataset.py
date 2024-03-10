from book_rec_helpers import BookInfo
import csv
import os
import pickle
import pandas as pd
import uuid

BOOKS_DATA_PATH = "archive/books_data.csv"
BOOKS_RATING_PATH = "archive/books_rating.csv"

def load_kaggle_data(num_reviews, min_rating, min_review_length):
    """
    Load data from the original Kaggle dataset.
    """
    all_books_dict = {}  # hashmap of id to book information

    books_df = pd.read_csv(BOOKS_DATA_PATH, nrows=100)
    books_df = books_df.dropna(subset=['description', 'categories'])
    books_df = books_df[books_df['description'].str.len() >= 20]
    books_df = books_df[books_df['categories'].str.len() >= 1]

    """
    with open(BOOKS_DATA_PATH, mode="r") as data_file:
        data_reader = csv.reader(data_file)
        start = 1

        # we already know every row has a unique value in this csv
        for row in data_reader:
            if start:
                start = 0
                continue
            skip = 0
            # if the description for this book is not filled out, skip this book
            if row[1] == "" or row[8] == "":
                skip = 1
            if skip:
                continue

            # clean up the list of authors and the cetegory (only 1 category ever listed)
            row[2] = row[2][1 : len(row[2]) - 1]
            row[2] = row[2].replace("'", "")
            row[8] = row[8][1 : len(row[8]) - 1]
            row[8] = row[8].replace("'", "")

            all_books_dict[row[0]] = BookInfo(row)
    """


    reviews_df = pd.read_csv(BOOKS_RATING_PATH, nrows=100)
    reviews_df = reviews_df.dropna(subset=['review/text'])
    reviews_df = reviews_df[reviews_df['Title'].isin(reviews_df['Title'])]
    reviews_df = reviews_df[reviews_df['review/text'].str.len() >= 1]
    # reviews_df['reviewId'] = reviews_df['ColumnToHash'].apply(lambda x: hash(x))
    reviews_df['reviewId'] = reviews_df.apply(lambda row: uuid.uuid3(uuid.NAMESPACE_DNS, f"{row['Title'], row['review/text']}"), axis=1)

    grouped = reviews_df.groupby('Title')['review/score'].mean().reset_index()
    books_df = pd.merge(grouped, books_df, on="Title", how="inner")


    with open(BOOKS_RATING_PATH, mode="r") as rating_file:
        rating_reader = csv.reader(rating_file)
        start = 1
        for row in rating_reader:
            if start:
                start = 0
                continue

            if row[1] in all_books_dict:
                # Note that for books that have multiple ids, we just pick one for now
                # also filter out reviews that gave a rating of less than 4 (don't want to overly confuse the model)
                current_book = all_books_dict[row[1]]
                if row[9] != "":
                    if current_book.id is None:
                        current_book.id = row[0]
                        current_book.amazon_link = "http://www.amazon.com/dp/" + str(
                            row[0]
                        )
                    current_book.amazon_average_book_score.append(float(row[6]))
                    if float(row[6]) >= 4 and len(row[9]) > min_review_length:
                        current_book.review_summaries.append(row[8])
                        current_book.reviews.append(row[9])

    all_books_list = []

    for key in all_books_dict:
        current_book = all_books_dict[key]
        # set average review value
        current_book.amazon_average_book_score = sum(
            current_book.amazon_average_book_score
        ) / len(current_book.amazon_average_book_score)
        # we want at least 30 reviews for a book
        if (
            len(current_book.reviews) < num_reviews
            or current_book.amazon_average_book_score < min_rating
        ):
            continue
        all_books_list.append(current_book)
    return all_books_list

def create_new_subset(num_reviews, min_rating, min_review_length):
    folder_path = "./defined_datasets"
    if not os.path.exists(folder_path):
        # Create the folder
        os.makedirs(folder_path)

    books = load_kaggle_data(float(num_reviews), float(min_rating), float(min_review_length))

    file_name = str(len(books)) + "_books_" + str(num_reviews) + "_min_reviews_" + str(min_rating) + "_min_rating_" + str(min_review_length) + "_min_review_length.pkl"
    file_path = "./defined_datasets/" + file_name
    with open(file_path, "wb") as f:
        pickle.dump(books, f)

if __name__ == "__main__":
    # num_reviews = input("Enter minumum number of reviews for each book: ")
    # min_rating = input("Enter minumum overall rating for each book: ")
    # min_review_length = input("Enter minumum length of a review: ")

    num_reviews = 30
    min_rating = 4.2
    min_review_length = 50
    create_new_subset(num_reviews, min_rating, min_review_length)
