import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
from sentence_transformer_embedding_function import SentenceTransformerEmbeddingFunction
import torch

# Constants for models
OPENAI_MODEL = "text-embedding-ada-002"
SENTENCE_TRANSFORMER_MODEL = "all-mpnet-base-v2"

def get_model_choice():
    """Get user's choice of embedding model."""
    print("\nAvailable models:")
    print(f"1. OpenAI ({OPENAI_MODEL})")
    print(f"2. Sentence Transformer ({SENTENCE_TRANSFORMER_MODEL})")
    while True:
        choice = input("Choose model (1 or 2): ").strip()
        if choice in ["1", "2"]:
            return "openai" if choice == "1" else "sentence_transformer"

def create_model(model_type):
    """Create the embedding model based on user choice."""
    if model_type == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name=OPENAI_MODEL
        )
    else:
        model = SentenceTransformerEmbeddingFunction(SENTENCE_TRANSFORMER_MODEL)
        if torch.cuda.is_available():
            model = model.to('cuda')
        return model

# Get user's choice of model
model_type = get_model_choice()
model = create_model(model_type)

# Connect to the persistent ChromaDB client and get the collection
client = PersistentClient(path="datastore")
collection = client.get_or_create_collection(
    name="my_documents",
    embedding_function=model
)

# Get the query from the user
query = input("Enter your search query: ")

# Perform a similarity search
results = collection.query(
    query_texts=[query],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print("what is result", results)
# Process and display results
# unique_files = {}
all_results = []
if results["ids"] and results["ids"][0]:
    for idx, doc_id in enumerate(results["ids"][0]):
        metadata = results["metadatas"][0][idx]
        content = results["documents"][0][idx]
        distance = results["distances"][0][idx] if "distances" in results else None
        similarity = 1 - distance if distance is not None else None
        

        if similarity is not None:
            all_results.append((similarity, metadata, content))
    sorted_results = sorted(all_results, key=lambda x: x[0], reverse=True)

    # Display results
    print("\nSearch Results:")
    print("---------------")
    for idx, (similarity, metadata, content) in enumerate(sorted_results):
        filename = metadata.get("source", "Unknown file")
        preview = content[:300] + "..." if len(content) > 300 else content
        
        print(f"Result {idx+1}:")
        print("File:", filename)
        print("Similarity Score:", similarity)
        print("Content Preview:")
        print(preview)
        print("-" * 50)
else:
    print("No matching results found.")
