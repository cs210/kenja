import chromadb
from chromadb.config import Settings
import csv
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="./chromadb_data", settings=Settings(anonymized_telemetry=False)
)
client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
BOOKS_RATING_PATH = "archive/books_rating.csv"
BOOKS_DATA_PATH = "archive/books_data.csv"
EMBEDDING_MODEL = "text-embedding-3-small"

"""
Extra TODOs:
- filter out low rated books (use google or amazon review values)
- only use reviews from amazon that give a rating of 3 or above
"""


"""
- only 5796 books considered right now

*** Notes *** :
- there are books that have isbn values but no title --> make sure to ignore these
- number of unique titles -> 212404
- number of unique isbn values -> 221790
- the id does not necessarily correlate to an isbn, but often does
    - I think that if the id starts with a value that is not a number, this means that
      it is not an isbn and is just Amazon's assigned value --> we will ignore these
      values and only work with books that
      start with numerical values
    - upon further investigation it appears (by just checking manually) that the above
      assumption is correct, however the same book can still have the same isbn number
      --> this only occurs for 3237 books out of 138,960 so in these cases we will make
      the assumption for now that the books are the same and just pick one of the isbn
      values
    - note that we will assume that no two books can have the same title (not sure if
      this is true, can only be a problem if the 3237 books above are actually
      different)
      - upon further investigation, popular books like harry potter are being tagged
        with these non-isbn ids these ids are the Amazon product numbers, or ASIN
- we will only consider books that have all values filled out in books_data.csv -->
  reduced number to *** 40635 *** books
- Adding the restriction of only considering isbns --> number of books is reduced
  to 26522
    - 832 books have multiple isbns, however, so the true value is 25,690
- upon further reflection, we have removed ratings count as a requried value for
  google, but will be keeping description

New notes:
- Ok, so it seems like books that do not have an ASIN and are being tracked with their
  isbns are actually the more obscure books, so switched to including ASIN values and
  got a TON more options (when using isbn --> none of the books had more than 1 review.
  Now, more than 60,000 books have 5 or more reviews)
- probably want to filter on genre more specifically at some point (only filtering out
  books with no genre label right now)
- Note: these values are for not fitlering out reviews with a rating less than 3:
    - at least 10 reviews: 33291
    - at least 15 reviews: 22880
    - at least 20 reviews: 17321
    - at least 25 reviews: 13760
- Note: filtering out reviews that are less than 4
    - at least 25 reviews: 10832
- Filtering out reviews that are less than 3:
    - at least 25 reviews: 12,077
- Filtering out reviews that are less than 4 and books with an average review rating
  less than 4:
    - at least 25 reviews: 8651
- Filtering out reviews that are less than 4 and books with an average review rating
  less than 4.2:
    - at least 30 reviews: 5796 books
- Need to make sure to filter out bad books later (my assumption right now, though, is
  that books with many reviews will have ok ratings)
 - will just remove reviews that are less than 3 for now as to not confuse the model
"""


class BookInfo:
    """
    Class for book objects
    """

    def __init__(self, row):
        # books data csv data
        self.title = row[0]
        self.description = row[1]
        self.authors = row[2]
        self.book_cover_url = row[3]
        self.google_preview_link = row[4]
        self.publisher = row[5]
        self.publish_date = row[6]
        self.google_info_link = row[
            7
        ]  # Note: I am not sure how this is different from the google preview link
        self.category = row[8]
        # self.average_google_rating = row[9] I'm not actually sure what this value
        # means, as it goes up to 4,900

        # books rating csv data
        self.id = None
        self.amazon_link = None
        self.amazon_average_book_score = (
            []
        )
        # this starts as a list of all the review scores, and then we take the
        # average at the end

        self.review_summaries = []
        self.reviews = []
        # Note: could also look at price later


def load_data():
    """
    Load data: currently in CSV file.
    """

    all_books_dict = {}  # hashmap of isbn to book information

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

            # clean up the list of authors and the category
            # (only 1 category ever listed)
            row[2] = row[2][1 : len(row[2]) - 1]
            row[2] = row[2].replace("'", "")
            row[8] = row[8][1 : len(row[8]) - 1]
            row[8] = row[8].replace("'", "")

            all_books_dict[row[0]] = BookInfo(row)

    with open(BOOKS_RATING_PATH, mode="r") as rating_file:
        rating_reader = csv.reader(rating_file)
        start = 1
        for row in rating_reader:
            if start:
                start = 0
                continue

            if row[1] in all_books_dict:
                # Note that for books that have multiple ids, we just pick one for now
                # also filter out reviews that gave a rating of less than 3
                # (don't want to overly confuse the model)
                current_book = all_books_dict[row[1]]
                if row[9] != "":
                    if current_book.id is None:
                        current_book.id = row[0]
                        current_book.amazon_link = "http://www.amazon.com/dp/" + str(
                            row[0]
                        )
                    current_book.amazon_average_book_score.append(float(row[6]))
                    if float(row[6]) >= 4:
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
            len(current_book.reviews) < 30
            or current_book.amazon_average_book_score < 4.2
        ):
            continue
        all_books_list.append(current_book)
    return all_books_list


def create_embedding(description):
    """
    Given a description, return an embedding.
    """
    return (
        client.embeddings.create(input=[description], model=EMBEDDING_MODEL)
        .data[0]
        .embedding
    )


def add_books(collection, book):
    """
    Add book to our vector database.
    """
    # do some prompt engineering on the input --> we will pass in the book description
    # and 3 reviews to start
    # we know that these reviews are associated with ratings of at least 4
    book_info = (
        "Title: " + book.title + "\n" + "Description: " + book.description + "\n"
    )
    for i in range(1, 4, 1):
        book_info += "Review " + str(i) + ":" + book.reviews[i] + "\n"

    collection.add(
        embeddings=[create_embedding(book_info)],
        documents=[book_info],
        metadatas=[
            {
                "title": book.title,
                "description": book.description,
                "category": book.category,
                "score": book.amazon_average_book_score,
                "link": book.amazon_link,
                "publisher": book.publisher,
                "publication_date": book.publish_date,
            }
        ],
        ids=[book.id],
    )


def find_book(collection, query):
    """
    Find a similar book based on our query.
    """
    embedding = create_embedding(query)
    results = collection.query(query_embeddings=[embedding], n_results=3)
    return results


def find_match(query):
    """
    Call all functions.
    """
    # Initialize all data
    collection = chroma_client.get_or_create_collection(name="books")

    if collection.count() == 0:
        print("populating data from file")
        # Initialize all data
        books = load_data()
        for i in range(len(books)):
            add_books(collection, books[i])
    else:
        print("Populating data from existing chromadb collection")

    # Find a similar wine
    results = find_book(collection, query)
    return results
    """
    books = load_data()
    collection = chroma_client.create_collection(name="books")
    for i in range(25):
        add_books(collection, books[i])

    # Find a similar wine
    results = find_book(collection, query)
    return results
    """
