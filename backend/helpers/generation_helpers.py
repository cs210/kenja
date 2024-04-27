from dotenv import load_dotenv
from openai import OpenAI
import re
from dotenv import load_dotenv
load_dotenv()

load_dotenv()
client = OpenAI()

EMBEDDING_MODEL = "text-embedding-3-small"

def get_generation(middle_search_results, option_count = 5):
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


def openai_create_embedding(text, is_document):
    """
    Given a description, return an embedding.
    """
    value = (client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
        .data[0]
        .embedding)
    type(value)
    return value