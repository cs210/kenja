import openai
from openai import OpenAI

# Set up your OpenAI API key
client = OpenAI()   
# Define wine tasting reviews
prompt1 = "Powerful, lush, fat, rich, concentrated, lusciously textured wine, with layers of blackberry, blue fruit, licorice, smoke, coffee, chocolate, vanilla and jam. A touch of heat, but there is such a wealth of fruit here, that heat is quickly smothered by another wave of ripe, sweet, dark fruits."
prompt2 = "Smoke, chocolate covered black cherries and coffee bean, plush, fleshy textures and a cocoa covered cassis and bitter chocolate finish are found in the already open wine."
prompt3 = "Powerful, lush and showy, the wine is packed with blackberries, blue fruits, dark cherries, chocolate, licorice and jammy fruits. The wine is rich, showy, polished and ready to go."
prompt4 = "Spice box, smoke, oak, truffle, blackberry liqueur and Espresso bean scents open to a thick, rich, spicy, lush, dense, intense, polished wine that ends with a fresh, deep, sensuous, cassis and black cherry finish."

reviews = [prompt1, prompt2, prompt3, prompt4]

# Embed the wine tasting reviews
embeddings = client.embeddings.create(
    model="text-embedding-3-small",
    input=reviews
)

# Calculate similarity (example using cosine similarity)
similarities = []
for i in range(len(embeddings.embeddings)):
    for j in range(i + 1, len(embeddings.embeddings)):
        similarity = openai.CosineSimilarity.create(
            engine="text-davinci-003",
            documents=[embeddings.embeddings[i], embeddings.embeddings[j]]
        )
        similarities.append((i, j, similarity.score))

# Sort similarities by score
similarities.sort(key=lambda x: x[2], reverse=True)

# Prompt the API to generate natural language response
prompt = f"Based on the wine tasting reviews, the similarities between them are as follows:\n"
for similarity in similarities[:min(5, len(similarities))]:
    prompt += f"- Review {similarity[0]+1} and Review {similarity[1]+1} are similar with a score of {similarity[2]:.2f}\n"

response = openai.Completion.create(
    engine="text-davinci-003",
    prompt=prompt,
    max_tokens=100
)

# Print the natural language response
print(response.choices[0].text.strip())
