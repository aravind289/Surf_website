from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
import os
from pathlib import Path

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the embedding function and data loader
embedder = SentenceTransformerEmbeddingFunction(model_name="sentence-transformers/all-MiniLM-L6-v2")
data_loader = ImageLoader()

# Connect to the ChromaDB client
client = chromadb.PersistentClient(
    path="datastore",  # ChromaDB path (same as in main.py)
)

# Get the collection
collection = client.get_collection(
    name="siftfiles",
    embedding_function=embedder,
    data_loader=data_loader,
)

@app.get("/api/search")
async def search(query: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    """
    Search for documents based on a semantic query.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
    
    Returns:
        A list of search results with document content and metadata
    """
    try:
        results = collection.query(
            query_texts=[query],
            n_results=limit,
            include=["metadatas", "documents", "distances"]
        )
        
        # Format the results for the frontend
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else None
                similarity = 1 - distance if distance is not None else None
                
                filepath = metadata.get("filepath", "Unknown path")
                filename = os.path.basename(filepath)
                file_type = metadata.get("type", Path(filepath).suffix[1:] if Path(filepath).suffix else "Unknown type")
                
                # Get document content if available
                content = results["documents"][0][i] if "documents" in results and results["documents"][0][i] else None
                
                # Create a preview (truncated content)
                preview = None
                if content:
                    preview = content[:200] + "..." if len(content) > 200 else content
                
                formatted_results.append({
                    "id": doc_id,
                    "filename": filename,
                    "filepath": filepath,
                    "filetype": file_type,
                    "similarity": similarity,
                    "preview": preview,
                    "content": content
                })
        
        return {"results": formatted_results}
    
    except Exception as e:
        return {"error": str(e), "results": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)