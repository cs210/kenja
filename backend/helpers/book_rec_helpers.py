from venv import create

# For chromadb
# __import__('pysqlite3')
# import sys
# sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
from chromadb.config import Settings
import pickle
from dotenv import load_dotenv
from openai import OpenAI
import pandas as pd
import uuid
import re

# for RAG embedding model
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased', model_max_length=8192)
model = AutoModel.from_pretrained('nomic-ai/nomic-embed-text-v1', trust_remote_code=True, rotary_scaling_factor=2)
model.eval()
model.to("cuda")


load_dotenv()
chroma_client = chromadb.PersistentClient(
    path="./chromadb_data", settings=Settings(anonymized_telemetry=False)
)
client = OpenAI()

# Constants for data
CONFIG_FILE = "config.json"
EMBEDDING_MODEL = "text-embedding-3-small"

def openai_create_embedding(text, is_document):
    """
    Given a description, return an embedding.
    """
    value = (client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        .data[0]
        .embedding)
    type(value)
    return value

def open_source_create_embeddings(texts_list, is_document):
    """
    Use the new local embeddings model to handle embeddings.
    """
    # Embed based on a document or a query
    if is_document:
        texts_list = ["search_document: " + item for item in texts_list]
    else:
        texts_list = ["search_query: " +  item for item in texts_list]
    
    # Mean pooling function to help with embeddings
    def mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    # Encode input and run through the model
    encoded_input = tokenizer(texts_list, padding=True, truncation=True, return_tensors='pt').to("cuda")
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Return the embeddings
    embeddings = mean_pooling(model_output, encoded_input['attention_mask'])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings


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
    embedding = open_source_create_embeddings([query], False).tolist()
    results = collection.query(query_embeddings=embedding, n_results=n_results)
    return results

def process_data(books_path, reviews_path, min_num_reviews, min_rating, min_review_length, min_description_length):
    """
    Load data from the original Kaggle dataset.
    """
    books_df = pd.read_csv(books_path)
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

def create_collections(books_path, reviews_path):
    """
    Create the embeddings for vector database search.
    """
    # We want to reset these collections, so try to get collection if it exists and delete it
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")
    descriptions_collection = chroma_client.delete_collection(name="book_descriptions")
    reviews_collection = chroma_client.delete_collection(name="book_reviews")
    middle_collection = chroma_client.delete_collection(name="middle_collection")
    
    descriptions_collection = chroma_client.get_or_create_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_or_create_collection(name="book_reviews")
    middle_collection = chroma_client.get_or_create_collection(name="middle_collection")

    # FIRST LEVEL

    books_df, reviews_df = process_data(books_path, reviews_path, 30, 4.2, 50, 20)

    reviews_df = reviews_df[reviews_df['Title'].isin(books_df['Title'])]

    reviews_df["helpful_votes"] = reviews_df["review/helpfulness"].apply(lambda x: str(x)[:x.find("/")])
    reviews_df["helpful_votes"] = pd.to_numeric(reviews_df["helpful_votes"])

    # only take the top 9 reviews for each book based on the number of helpful upvotes for now
    top_reviews_df = reviews_df.groupby("Title").apply(lambda x: x.nlargest(9, "helpful_votes")).reset_index(drop=True)

    books_metadatas = books_df.to_dict(orient="records")
    reviews_metadatas = top_reviews_df.to_dict(orient="records")

    start_index = 0
    next_index = 5
    description_list = books_df["description"].tolist()
    torch.cuda.empty_cache()
    descriptions_embeddings = []
    while (start_index < len(description_list)):
        print(start_index)
        current_slice = description_list[start_index:next_index]
        slice_embeddings = open_source_create_embeddings(current_slice, True).tolist()
        descriptions_embeddings += slice_embeddings
        start_index = next_index
        next_index += 5
    
    start_index = 0
    next_index = 5
    reviews_list = top_reviews_df["review/text"].tolist()
    torch.cuda.empty_cache()
    reviews_embeddings = []
    while (start_index < len(reviews_list)):
        print(start_index)
        current_slice = reviews_list[start_index:next_index]
        slice_embeddings = open_source_create_embeddings(current_slice, True).tolist()
        reviews_embeddings += slice_embeddings
        start_index = next_index
        next_index += 5

    books_ids = books_df["Title"].tolist()
    reviews_ids = top_reviews_df["reviewId"].tolist()

    books_documents = books_df["description"].tolist()
    reviews_documents = top_reviews_df["review/text"].tolist()

    add_to_collection(descriptions_collection, descriptions_embeddings, books_documents, books_metadatas, books_ids)

    add_to_collection(reviews_collection, reviews_embeddings, reviews_documents, reviews_metadatas, reviews_ids)

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

    start_index = 0
    next_index = 5
    middle_list = middle_df["combined_text"].tolist()
    torch.cuda.empty_cache()
    middle_embeddings = []
    while (start_index < len(reviews_list)):
        print(start_index)
        current_slice = reviews_list[start_index:next_index]
        slice_embeddings = open_source_create_embeddings(current_slice, True).tolist()
        middle_embeddings += slice_embeddings
        start_index = next_index
        next_index += 5
    middle_ids = middle_df["Title"].tolist()
    middle_documents = middle_df["combined_text"].tolist()
    add_to_collection(middle_collection, middle_embeddings, middle_documents, middle_metadatas, middle_ids)


def find_match(query, update_collections = False):
    """
    Call all functions.
    """
    descriptions_collection = chroma_client.get_collection(name="book_descriptions")
    reviews_collection = chroma_client.get_collection(name="book_reviews")
    middle_collection = chroma_client.get_collection(name="middle_collection")
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


