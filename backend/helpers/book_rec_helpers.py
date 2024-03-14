from venv import create
import chromadb
from chromadb.config import Settings
import pickle
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import uuid
import re

load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="./chromadb_data", settings=Settings(anonymized_telemetry=False)
)
client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
EMBEDDING_MODEL = "text-embedding-3-small"
BOOKS_DATASET_PATH = "./defined_datasets/books_df_4494_books_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"
REVIEWS_DATASET_PATH = "./defined_datasets/reviews_df_448893_total_reviews_30_min_num_reviews_4.2_min_rating_20_min_description_length_50_min_review_length.csv"

def create_embedding(text):
    """
    Given a description, return an embedding.
    """
    return (
        client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        .data[0]
        .embedding
    )

def add_to_collection(collection, embeddings, documents, metadatas, ids):
    """
    Add an embedding to the appropriate vector database.
    """
    collection.add(
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
        ids=ids,
    )

def embedding_search(collection, query, n_results):
    embedding = create_embedding(query)
    results = collection.query(query_embeddings=embedding, n_results=n_results)
    return results


def find_match(query, update_collections = False):
    """
    Call all functions.
    """
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")
    if update_collections:
        chroma_client.delete_collection(name="book_descriptions")
        chroma_client.delete_collection(name="book_reviews")
        chroma_client.delete_collection(name="middle_collection")
        descriptions_collection = chroma_client.create_collection(name="book_descriptions")
        reviews_collection = chroma_client.create_collection(name="book_reviews")
        middle_collection = chroma_client.create_collection(name="middle_collection")

    if reviews_collection.count() == 0:
        print("populating data from file")

        # FIRST LEVEL
        books_df = pd.read_csv(BOOKS_DATASET_PATH, nrows=10)

        reviews_df = pd.read_csv(REVIEWS_DATASET_PATH)
        reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

        reviews_df["helpful_votes"] = reviews_df["review/helpfulness"].apply(lambda x: str(x)[:x.find("/")])
        reviews_df["helpful_votes"] = pd.to_numeric(reviews_df["helpful_votes"])

        # only take the top 10 reviews for each book based on the number of helpful upvotes for now
        top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(10, "helpful_votes")).reset_index(drop=True)

        books_metadatas = books_df.to_dict(orient="records")
        reviews_metadatas = top_reviews_df.to_dict(orient="records")
        
        books_df["description_embedding"] = books_df["description"].apply(lambda x: create_embedding(x))
        top_reviews_df["review_embedding"] = top_reviews_df["review/text"].apply(lambda x: create_embedding(x))

        books_embeddings = books_df["description_embedding"].tolist()
        reviews_embeddings = top_reviews_df["review_embedding"].tolist()

        books_ids = books_df["Title"].tolist()
        reviews_ids = top_reviews_df["reviewId"].tolist()

        books_documents = books_df["description"].tolist()
        reviews_documents = top_reviews_df["review/text"].to_list()

        add_to_collection(reviews_collection, reviews_embeddings, reviews_documents, reviews_metadatas, reviews_ids)
        add_to_collection(descriptions_collection, books_embeddings, books_documents, books_metadatas, books_ids)

        # SECOND LEVEL
        exclude = ["description_embedding", "description_length"]
        middle_df = books_df[[col for col in books_df.columns if col not in exclude]]
        middle_df["description"] = "Description: " + middle_df["description"] + "\n\n"

        top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(4, "helpful_votes")).reset_index(drop=True)

        top_reviews_df = top_reviews_df[["Title", "review/text"]]
        top_reviews_df["review/text"] = "Review: " + top_reviews_df["review/text"]
        top_reviews_df = top_reviews_df.groupby("Title").agg({'review/text': lambda x: '\n\n'.join(map(str, x))}).reset_index()

        middle_df = pd.merge(middle_df, top_reviews_df, on="Title", how="inner")
        
        middle_df["combined_text"] = middle_df["description"] + middle_df["review/text"]
        middle_df = middle_df.drop("description", axis=1)
        middle_df = middle_df.drop("review/text", axis=1)
        middle_df["text_length"] = middle_df["combined_text"].apply(lambda x: len(str(x)))

        middle_metadatas = middle_df.to_dict(orient="records")
        middle_df["combined_text_embedding"] = middle_df["combined_text"].apply(lambda x: create_embedding(x))
        middle_embeddings = middle_df["combined_text_embedding"].tolist()
        middle_ids = middle_df["Title"].tolist()
        middle_documents = middle_df["combined_text"].to_list()
        add_to_collection(middle_collection, middle_embeddings, middle_documents, middle_metadatas, middle_ids)
    else:
        print("Populating data from existing chromadb collection")
    review_search_results = embedding_search(reviews_collection, query, 20)
    titles_list = [dictionary["Title"] for dictionary in review_search_results["metadatas"][0]]
    titles_list = list(set(titles_list)) # there is a chance that the same book will appear multiple times
    description_search_results = embedding_search(descriptions_collection, query, 10)
    titles_list.extend(description_search_results["ids"][0])
    titles_list = list(set(titles_list)) # same book could have been given by both reviews and descriptions

    # SECOND LEVEL
    extract_dict = middle_collection.get(ids=titles_list, include=["embeddings", "documents", "metadatas"])
    # probably want to be more clever with this name
    client_name = str(uuid.uuid1())
    extract_collection = chroma_client.create_collection(name=client_name)
    add_to_collection(extract_collection, extract_dict["embeddings"], extract_dict["documents"], extract_dict["metadatas"], extract_dict["ids"])
    option_count = 5
    middle_search_results = embedding_search(extract_collection, query, option_count)
    chroma_client.delete_collection(name=client_name)
    
    '''super_prompt_engineer = (
f"""Hey ChatGPT. I have a question for you. of the {option_count} words I am hoping for you to provide the top 3 options you think best matches the request/description
{query}

These are the options\n\n
""")'''

    '''super_prompt_engineer = 
    """
    Pretend you are an expert at books 
    """'''

    system_prompt = (
        f"""
        You are are an expert at reading books. In particular, you have read every book that has ever been published, and have also perused sites like Goodreads.
        """
    )

    super_prompt_engineer = (
        f"""
        Now, given a request of an ideal book, you will be given {option_count} books and asked to provide the top 3 options. In particular, each of the options will be labeled `Option #`, and will have a corresponding 
        description and several reviews of the book. After parsing through all of this information, please first explain your reasoning behind your decision-making. After explaining yourself, then return the options,
        as well as the reasons for choosing each option, in the following format. Please include all of the dashes, and make sure to always include three options:

        Reasoning:
        <REASONING_FOR_CHOICES>

        Options:
        - Option #<FIRST_CHOICE>: <TITLE_OF_FIRST_CHOICE>
        - Reasoning for #<FIRST_CHOICE>: <REASONING_FOR_FIRST_CHOICE>
        - Option #<SECOND_CHOICE>: <TITLE_OF_SECOND_CHOICE>
        - Reasoning for #<SECOND_CHOICE>: <REASONING_FOR_SECOND_CHOICE>
        - Option #<THIRD_CHOICE>
        - Reasoning for #<THIRD_CHOICE>: <REASONING_FOR_THIRD_CHOICE>

        Each of the options are now below:
        """
    )

    book_features = zip(middle_search_results["documents"][0])
    for i, defining_tuple in enumerate(book_features):
        super_prompt_engineer += (
f"""
Option #{i}:
{defining_tuple[0]}


"""
        )
    
    # Make the call!
    response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": super_prompt_engineer}
    ]
    )
    
    # Collect all of the data
    options = []
    reasonings = []
    d = {}
    for i in range(len(middle_search_results["documents"][0])):
        options.append(f"- Option #{i}")
        reasonings.append(f"- Reasoning for #{i}")
        d[f"- Option #{i}"] = middle_search_results["metadatas"][0][i]

    # Get the text
    text = response.choices[0].message.content

    # Create a regex pattern to search for the options and reasonings
    pattern = '|'.join(re.escape(option) for option in options)
    reasoning_pattern = '|'.join(re.escape(reasoning) for reasoning in reasonings)

    # Find all matches in the string, along with their positions
    matches = [(m.start(), m.group()) for m in re.finditer(pattern, text)]
    reasoning_matches = [(m.start(), m.group()) for m in re.finditer(reasoning_pattern, text)]

    # Get the last match, if there are any matches
    last_matches = [i[1] for i in matches][-3:]
    reasoning_matches = [i for i in reasoning_matches][-3:]

    # Extract the right text
    for i in range(len(reasoning_matches)):
        new_text = text[reasoning_matches[i][0]:]
        next_section = new_text.find("\n")
        gpt_review = new_text[len("- Reasoning for #1: "):next_section]
        last_match = last_matches[i]
        d[last_match]['gpt_review'] = gpt_review

    return [d[last_match] for last_match in last_matches]


