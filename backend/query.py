import os
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# Initialize the OpenAI embedding function (using text-embedding-ada-002)
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"
)

# Connect to the persistent ChromaDB client and get the collection
client = PersistentClient(path="datastore")
collection = client.get_or_create_collection(
    name="my_documents",
    embedding_function=openai_ef
)

# Get the query from the user
query = input("Enter your search query: ")

# Perform a similarity search (query embedding is generated on the fly)
# Here we ask for 3 results; adjust n_results as needed.
results = collection.query(
    query_texts=[query],
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print(results)
# Check if there are any matching results
# Create a list to store results along with computed similarity
all_results = []
if results["ids"] and results["ids"][0]:
    for idx, doc_id in enumerate(results["ids"][0]):
        metadata = results["metadatas"][0][idx]
        content = results["documents"][0][idx]
        distance = results["distances"][0][idx] if "distances" in results else None
        # Compute similarity as (1 - distance) assuming cosine distance
        similarity = 1 - distance if distance is not None else None
        
        # Append result as a tuple: (similarity, metadata, content)
        if similarity is not None:
            all_results.append((similarity, metadata, content))
    
    # Sort results by similarity descending (highest similarity first)
    sorted_results = sorted(all_results, key=lambda x: x[0], reverse=True)
    
    print("\nSearch Results (sorted by similarity):\n" + "="*50)
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
    print("No matching documents found.")
