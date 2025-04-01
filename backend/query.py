import chromadb 
from chromadb import Settings
from chromadb.utils.data_loaders import ImageLoader
import sys
import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

def main():
    # Initialize the all-MiniLM-L6-v2 model for embeddings (smaller and faster)
    embedder = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
    data_loader = ImageLoader()

    # Connect to the ChromaDB client
    client = chromadb.PersistentClient(
        path="datastore",  # ChromaDB path (same as in main.py)
    )

    # Get the collection
    try:
        collection = client.get_collection(
            name="siftfiles",
            embedding_function=embedder,
            data_loader=data_loader,
        )
    except Exception as e:
        print(f"Error: Could not get collection: {e}")
        print("Make sure you've run main.py to index files first.")
        return

    # Get query from command line arguments or prompt the user
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("Enter your search query: ")


    # print(f"\nSearching for: '{query}'")
    # print("-" * 50)

    # Perform the query
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5
        )
        if results["documents"] and len(results["documents"][0]) > 0:
            print(f"Found {len(results['documents'][0])} result(s):\n")
            # Extract the most similar document (top result)
            doc_id = results["ids"][0][0]  # Top result ID
            metadata = results["metadatas"][0][0]  # Top result metadata
            distance = results["distances"][0][0] if "distances" in results else None
            similarity = 1 - distance if distance is not None else None

            filepath = metadata.get("filepath", "Unknown path")
            file_type = metadata.get("type", "Unknown type")

            print(f"Top Result - {os.path.basename(filepath)} ({file_type})")
            print(f"  Path: {filepath}")
            print(f"  Similarity: {similarity:.4f}" if similarity is not None else "  Similarity: Unknown")

            # Preview the document content (if it's a text document)
            if "documents" in results and results["documents"][0][0]:
                content = results["documents"][0][0]
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  Preview: {preview}")

        else:
            print("No results found for your query.")

        # for i, doc_id in enumerate(results["ids"][0]):
        #     print("what is the distance",results["distances"][0][i])
        #     print("what is results ----------------",results["metadatas"])
        #     print(results.keys())
            # if results["distances"][0][i]*100 > :
                
            # else:
            #     print("no result found")
        
        # # Display results
        # if results["ids"] and len(results["ids"][0]) > 0:
        #     print(f"Found {len(results['ids'][0])} results:\n")
            
        #     for i, doc_id in enumerate(results["ids"][0]):
        #         metadata = results["metadatas"][0][i]
        #         distance = results["distances"][0][i] if "distances" in results else None
        #         similarity = 1 - distance if distance is not None else None
                
        #         filepath = metadata.get("filepath", "Unknown path")
        #         file_type = metadata.get("type", "Unknown type")
                
        #         print(f"Result #{i+1} - {os.path.basename(filepath)} ({file_type})")
        #         print(f"  Path: {filepath}")
        #         print(f"  Similarity: {similarity:.4f}" if similarity is not None else "  Similarity: Unknown")
                
        #         # If it's a text document, show a preview
        #         if "documents" in results and results["documents"][0][i]:
        #             content = results["documents"][0][i]
        #             preview = content[:200] + "..." if len(content) > 200 else content
        #             print(f"  Preview: {preview}")
                
        #         print()
        # else:
        #     print("No results found for your query.")
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    main()
