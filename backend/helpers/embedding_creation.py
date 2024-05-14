# For making embeddings and such
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel
import torch
from tqdm import tqdm

tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased", model_max_length=8192)
model = AutoModel.from_pretrained(
    "nomic-ai/nomic-embed-text-v1", trust_remote_code=True, rotary_scaling_factor=2
)
if torch.cuda.is_available():
        model.to("cuda")
model.eval()

def open_source_create_embeddings(texts_list, is_document):
    """
    Use the new local embeddings model to handle embeddings.
    """
    # Embed based on a document or a query
    if is_document:
        texts_list = ["search_document: " + item for item in texts_list]
    else:
        texts_list = ["search_query: " + item for item in texts_list]

    # Mean pooling function to help with embeddings
    def mean_pooling(model_output, attention_mask):
        token_embeddings = model_output[0]
        input_mask_expanded = (
            attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        )
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
            input_mask_expanded.sum(1), min=1e-9
        )

    # Encode input and run through the model
    encoded_input = tokenizer(
        texts_list, padding=True, truncation=True, return_tensors="pt"
    )
    if torch.cuda.is_available():
        encoded_input = encoded_input.to("cuda")
    with torch.no_grad():
        model_output = model(**encoded_input)

    # Return the embeddings
    embeddings = mean_pooling(model_output, encoded_input["attention_mask"])
    embeddings = F.normalize(embeddings, p=2, dim=1)
    return embeddings

# A helper function to populate a given collection with embeddings
def create_collection_embeddings(collection, feature, documents, metadatas, ids):
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    desc = feature + " embedding creation progress"
    for i in tqdm(range(0, len(ids), 5), desc=desc):
        # Find start and stop
        start_index, next_index = i, min(i+5, len(ids))
        current_documents = documents[start_index:next_index]
        current_metadatas = metadatas[start_index:next_index]
        current_ids = ids[start_index:next_index]

        current_embeddings = open_source_create_embeddings(
            current_documents, True
        ).tolist()

        collection.add(
            embeddings=current_embeddings,
            documents=current_documents,
            metadatas=current_metadatas,
            ids=current_ids,
        )