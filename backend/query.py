"""
Query script for testing semantic search on indexed files
"""
import chromadb
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
import sys
import os
from pathlib import Path

def main():
    # Initialize the embedding function and data loader
    embedder = OpenCLIPEmbeddingFunction()
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

    print(f"\nSearching for: '{query}'")
    print("-" * 50)

    # Perform the query
    try:
        results = collection.query(
            query_texts=[query],
            n_results=5,
            include=["metadatas", "documents", "distances"]
        )
        
        # Display results
        if results["ids"] and len(results["ids"][0]) > 0:
            print(f"Found {len(results['ids'][0])} results:\n")
            
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else None
                similarity = 1 - distance if distance is not None else None
                
                filepath = metadata.get("filepath", "Unknown path")
                file_type = metadata.get("type", "Unknown type")
                
                print(f"Result #{i+1} - {os.path.basename(filepath)} ({file_type})")
                print(f"  Path: {filepath}")
                print(f"  Similarity: {similarity:.4f}" if similarity is not None else "  Similarity: Unknown")
                
                # If it's a text document, show a preview
                if "documents" in results and results["documents"][0][i]:
                    content = results["documents"][0][i]
                    preview = content[:200] + "..." if len(content) > 200 else content
                    print(f"  Preview: {preview}")
                
                print()
        else:
            print("No results found for your query.")
    except Exception as e:
        print(f"Error during search: {e}")

if __name__ == "__main__":
    main()
