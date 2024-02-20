import chromadb
from chromadb.config import Settings
import csv
from dotenv import load_dotenv
from openai import OpenAI

# load_dotenv()
# chroma_client = chromadb.Client(Settings(anonymized_telemetry=False))
# client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
BOOKS_RATING_PATH = "archive/books_rating.csv"
BOOKS_DATA_PATH = "archive/books_data.csv"
EMBEDDING_MODEL = "text-embedding-3-small"

"""
- only 26,522 books considered right now

*** Notes *** : 
- there are books that have isbn values but no title --> make sure to ignore these
- number of unique titles -> 212404
- number of unique isbn values -> 221790
- the id does not necessarily correlate to an isbn, but often does
    - I think that if the id starts with a value that is not a number, this means that it is not an isbn
      and is just Amazon's assigned value --> we will ignore these values and only work with books that 
     start with numerical values
    - upon further investigation it appears (by just checking manually) that the above assumption is
      correct, however the same book can still have the same isbn number --> this only occurs for 
      3237 books out of 138,960 so in these cases we will make the assumption for now that the books are
      the same and just pick one of the isbn values
    - note that we will assume that no two books can have the same title (not sure if this is true, can
      only be a problem if the 3237 books above are actually different)
- we will only consider books that have all values filled out in books_data.csv --> reduced number to *** 40635 *** books
- Adding the restriction of only considering isbns --> number of books is reduced to 26522
    - 832 books have multiple isbns, however, so the true value is 25,690
"""

class BookInfo:
    """
    Class for wine objects
    """
    def __init__(self, row):


        """
        self.raw_content = row[1:] # the id is the key in the hashmap
        self.amazon_link = "http://www.amazon.com/dp/" + str(row[0])
        self.title = row[1]
        # initialize a list of all the review ratings, summaries, and the reviews themselves
        self.book_score = [float(row[6])]
        self.review_summaries = [row[8]]
        self.reviews = [row[9]] 
        # row[2] is price --> intentionally not including for now
        # row[3] is user id --> not wanted information
        # row[4] is profile name --> not wanted information
        # row[5] is helpful rating of the review --> confused about how this is structured in the dataset, maybe use later
        # row[7] is review time --> not wanted information
        """

def load_data():
    """
    Load data: currently in CSV file.
    """

    all_books_dict = {} # hashmap of isbn to book information

    with open(BOOKS_DATA_PATH, mode='r') as data_file:
        data_reader = csv.reader(data_file)
        start = 1

        # we already know every row has a unique value here
        for row in data_reader:
            if start:
                start = 0
                continue
            skip = 0
            for i in range(len(row)):
                if row[i] == "":
                    skip = 1
                    break
            if skip:
                continue
            all_books_dict[row[0]] = 0

    all_isbns_dict = {}

    with open(BOOKS_RATING_PATH, mode='r') as file:
        reader = csv.reader(file)
        
        index = 0
        for row in reader:
            if index == 0:
                index += 1
                continue
            # if row[1] in all_titles_dict and row[0] not in all_books_dict:
            #     print(row[1])
        

            # if row[0] not in all_books_dict and row[0][0].isnumeric():
            #     all_books_dict[row[0]] = 1
            #     if row[1] not in all_titles_dict:
            #         all_titles_dict[row[1]] = 1
            #     else:
            #         num_same_title_different_isbn += 1

            if row[1] in all_books_dict:
                if row[0] not in all_isbns_dict and row[0][0].isnumeric():
                    all_isbns_dict[row[0]] = 1
                    all_books_dict[row[1]] += 1
    total_repeated = 0
    for key in all_books_dict:
        if all_books_dict[key] > 1:
            total_repeated += 1
    print(total_repeated)
    print(len(all_isbns_dict.keys()))
    print(len(all_books_dict.keys()))
    # print(len(all_books_dict.keys()))
    # print(len(all_books_dict.keys()) - num_here)
    #         if row[0] not in all_books_dict:
    #             all_books_dict[row[0]] = BookInfo(row)
    #         else:
    #             all_books_dict[row[0]].book_score.append(float(row[6]))
    #             all_books_dict[row[0]].review_summaries.append(row[8])
    #             all_books_dict[row[0]].reviews.append(row[9])
    #         if index == 1000:
    #             break
    #         index += 1
    # all_books_list = []
    # for key in all_books_dict:
    #     all_books_dict[key].isbn = key
    #     all_books_dict[key].book_score = str(sum(all_books_dict[key].book_score) / len(all_books_dict[key].book_score))
    #     all_books_list.append(all_books_dict[key])
    # return all_books_list

def create_embedding(description):
    """
    Given a description, return an embedding.
    """
    return client.embeddings.create(input = [description], model=EMBEDDING_MODEL).data[0].embedding

def add_wines(collection, book):
    """
    Add wine to our vector database.
    """
    collection.add(
        embeddings=[create_embedding(wine.description)],
        documents=[wine.description],
        metadatas=[{"designation": wine.designation, "variety": wine.variety, "winery": wine.winery}],
        ids=[book.isbn]
    )

def find_wine(collection, query):
    """
    Find a similar wine based on our query.
    """
    embedding = create_embedding(query)
    results = collection.query(
        query_embeddings=[embedding],
        n_results=3
    )
    return results

def find_match(query):
    """
    Call all functions.
    """
    # Initialize all data
    books = load_data()
    collection = chroma_client.create_collection(name="books")
    for i in range(25):
        add_wines(collection, books[i])

    # Find a similar wine
    results = find_wine(collection, query)
    return results