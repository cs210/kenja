import pandas as pd
import uuid

BOOKS_PATH = "./archive/books_data.csv"
REVIEWS_PATH = "./archive/books_rating.csv"

def process_book_data(books_path, reviews_path, min_num_reviews, min_rating, min_review_length, min_description_length, merge):
    """
    Load data from the original book Kaggle dataset.
    """
    books_df = pd.read_csv(books_path)

    # only keep books that have descriptions that meet the required length
    books_df = books_df.dropna(subset=['description', 'categories'])
    books_df = books_df[books_df['description'].str.len() >= min_description_length]

    reviews_df = pd.read_csv(reviews_path)
    reviews_df = reviews_df.dropna(subset=['review/text'])

    # remove any duplicate reviews
    reviews_df = reviews_df.drop_duplicates(subset=["review/text"])

    # only keep books that haven't already been filtered out
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # give the review an id using deterministic hash function
    reviews_df['reviewId'] = reviews_df.apply(lambda row: str(uuid.uuid3(uuid.NAMESPACE_DNS, f"{row['Title'], row['review/text']}")), axis=1)

    # drop any books that don't have the specified minimum average rating
    average_rating_df = reviews_df.groupby('Title')['review/score'].mean().reset_index()
    average_rating_df = average_rating_df[average_rating_df["review/score"] >= min_rating]
    average_rating_df = average_rating_df.rename(columns = {"review/score": "average_rating"})
    books_df = pd.merge(average_rating_df, books_df, on="Title", how="inner")

    # make sure that the books df and reviews df both have the same books 
    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    # only keep reviews that are long enough
    reviews_df = reviews_df[reviews_df["review/text"].str.len() >= min_review_length]

    # only want reviews that give a score of at least 4
    # (books could have receieved an average rating above the specified average rating, 
    # but we don't want to keep these reviews)
    reviews_df = reviews_df[reviews_df["review/score"] >= 4]

    # want at least min_num_reviews for a book
    title_counts = reviews_df["Title"].value_counts()
    title_counts = title_counts[title_counts >= min_num_reviews]
    enough_reviews_df = pd.DataFrame({"Title":title_counts.index})
    reviews_df = reviews_df[reviews_df['Title'].isin(enough_reviews_df['Title'])]

    # add the review length as an entry
    reviews_df["review_length"] = reviews_df["review/text"].apply(lambda x: len(str(x)))

    reviews_df["helpful_votes"] = reviews_df["review/helpfulness"].apply(lambda x: str(x)[:x.find("/")])
    reviews_df["helpful_votes"] = pd.to_numeric(reviews_df["helpful_votes"])
    # Only take the top 10 reviews for each book based on the number of helpful upvotes for now
    reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(10, "helpful_votes")).reset_index(drop=True)

    # update books df for any titles removed from reviews df
    books_df = books_df[books_df['Title'].isin(reviews_df['Title'])]

    # add the description length as an entry
    books_df["description_length"] = books_df["description"].apply(lambda x: len(str(x)))

    print(len(books_df))

    if merge: 
        # combine the two dataframes and create a new, structured csv
        structered_books_csv_df = pd.merge(books_df, reviews_df, on="Title", how="outer")
        structered_books_csv_df.to_csv(".//structured_book_dataset.csv", index=False)
    else: 
        books_df.to_csv("./books_datasets/mini_books_data.csv", index=False)
        reviews_df.to_csv("./books_datasets/mini_books_rating.csv", index=False)

# Parameters of 60, 4.9, 50, 20 for mini dataset size of 27
process_book_data(BOOKS_PATH, REVIEWS_PATH, 60, 4.9, 50, 20, True)