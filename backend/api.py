from fastapi import FastAPI, Query, Body, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import chromadb
from chromadb.utils import embedding_functions
import os
import time
import tiktoken
import PyPDF2
import docx
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter

app = FastAPI()

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name="text-embedding-ada-002"
)

# Ensure datastore directory exists with proper permissions
datastore_path = Path("datastore").absolute()



# Create a fresh datastore directory
try:
    datastore_path.mkdir(parents=True, exist_ok=True)
    # Set permissions to ensure we can write to it
    os.chmod(str(datastore_path), 0o777)
    print(f"Created datastore directory at {datastore_path}")
except Exception as e:
    print(f"Error creating datastore directory: {e}")
    raise

# Connect to the ChromaDB client with settings optimized for reliability
try:
    client = chromadb.PersistentClient(
        path=str(datastore_path),  # ChromaDB path
        settings=chromadb.Settings(
            anonymized_telemetry=False,  # Disable telemetry
            allow_reset=True,  # Allow resetting the database if needed
        )
    )
    print("Successfully connected to ChromaDB")
except Exception as e:
    print(f"Error connecting to ChromaDB: {e}")
    raise

# Get or create the collection
try:
    collection = client.get_collection(
        name="my_documents",
        embedding_function=openai_ef,
    )
except Exception as e:
    print(f"Collection not found, will be created when indexing starts: {e}")
    collection = None

# Global variables to track embedding progress
embedding_status = {
    "is_running": False,
    "total_files": 0,
    "processed_files": 0,
    "current_file": "",
    "progress_percentage": 0,
    "status": "idle",  # idle, running, completed, error
    "error": None
}

# Helper functions for text extraction and embedding
def initialize_encoder(model_name="text-embedding-ada-002"):
    """Initialize and return the tiktoken encoder."""
    return tiktoken.encoding_for_model(model_name)

def count_tokens(text: str, encoding) -> int:
    """Count tokens using the provided tiktoken encoder."""
    return len(encoding.encode(text))

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text from a DOCX file using python-docx."""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: Path) -> str:
    """Reads text from a TXT file."""
    try:
        return file_path.read_text(errors="ignore")
    except Exception as e:
        print(f"Error extracting text from TXT {file_path}: {e}")
        return ""
    
# have to do csv , excel as well. have to see if there is a process to just use one helper function to process everything

# Models for API requests and responses
class FolderList(BaseModel):
    folders: List[str]

class IndexingRequest(BaseModel):
    folders: List[str]
    custom_folders: List[str] = []

class IndexingStatus(BaseModel):
    is_running: bool
    total_files: int
    processed_files: int
    current_file: str
    progress_percentage: float
    status: str
    error: Optional[str] = None

# Function to index files from selected folders
def index_files_from_folders(folders: List[str], custom_folders: List[str]):
    global embedding_status, collection
    
    try:
        # Initialize the encoder and text splitter
        # encoding = 
        initialize_encoder("text-embedding-ada-002")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=8000,    # Larger chunks for faster processing
            chunk_overlap=200,   # Overlap to preserve context
            separators=["\n\n", "\n", " ", ""]
        )
        
        # Create collection if it doesn't exist or get the existing one
        try:
            collection = client.get_collection(
                name="my_documents",
                embedding_function=openai_ef,
            )
            print("Using existing collection")
        except Exception as e:
            print(f"No existing collection found: {e}")
            collection = client.create_collection(
                name="my_documents",
                embedding_function=openai_ef,
                metadata={"description": "Indexed documents for semantic search"}
            )
            print("Created fresh collection for document indexing")
        
        # Get list of already indexed files
        try:
            # Create a metadata collection if it doesn't exist
            try:
                metadata_collection = client.get_collection("file_metadata")
            except:
                metadata_collection = client.create_collection("file_metadata")
            
            # Get all indexed file paths and their modification times
            results = metadata_collection.get()
            print("what is the metadata",results)
            indexed_files = {}
            if results and "metadatas" in results and results["metadatas"]:
                for metadata in results["metadatas"]:
                    if "filepath" in metadata:
                        indexed_files[metadata["filepath"]] = metadata.get("last_modified", 0)
        except Exception as e:
            print(f"Error getting indexed files: {e}")
            indexed_files = {}
        
        # Prepare list of directories to process
        # [rest of the directory preparation code remains unchanged]
        # Prepare list of directories to process
        directories = []
        home_dir = Path(os.environ.get("HOME"))

        # Add standard folders
        folder_mapping = {
            "downloads": home_dir / "Downloads",
            "documents": home_dir / "Documents",
            "desktop": home_dir / "Desktop"
        }

        for folder in folders:
            if folder.lower() in folder_mapping and folder_mapping[folder.lower()].exists():
                directories.append(folder_mapping[folder.lower()])

        # Add custom folders
        for custom_folder in custom_folders:
            folder_path = Path(custom_folder)
            if folder_path.exists() and folder_path.is_dir():
                directories.append(folder_path)
        
        # Count total files to process (only new or modified files)
        total_files = 0
        files_to_process = []
        for directory in directories:
            # Process files recursively through all subdirectories
            for file in directory.glob("**/*"):
                if file.is_file() and file.suffix.lower() in [".pdf", ".docx", ".txt"]:
                    filepath_str = str(file.absolute())
                    last_modified = file.stat().st_mtime
                    
                    # Check if file is new or modified
                    if filepath_str not in indexed_files or indexed_files[filepath_str] < last_modified:
                        total_files += 1
                        files_to_process.append((file, last_modified))
        
        embedding_status["total_files"] = total_files
        embedding_status["processed_files"] = 0
        embedding_status["is_running"] = True
        embedding_status["status"] = "running"
        
        # Process each file
        for file, last_modified in files_to_process:
            if not embedding_status["is_running"]:
                # Stop if cancelled
                embedding_status["status"] = "cancelled"
                return
            
            filepath_str = str(file.absolute())
            
            if file.suffix.lower() == ".pdf":
                text = extract_text_from_pdf(file)
            elif file.suffix.lower() == ".docx":
                text = extract_text_from_docx(file)
            elif file.suffix.lower() == ".txt":
                text = extract_text_from_txt(file)
            else:
                continue  # Skip unsupported file types
            
            if not text:
                continue
            
            # Update status
            embedding_status["current_file"] = str(file.name)
            
            # Delete existing chunks for this file if any
            try:
                existing_chunks = collection.get(
                    where={"source": filepath_str}
                )
                if existing_chunks and existing_chunks["ids"]:
                    collection.delete(ids=existing_chunks["ids"])
            except Exception as e:
                print(f"Error removing existing chunks: {e}")
            
            # Split text into chunks
            chunks = text_splitter.split_text(text)
            
            # Add chunks to collection
            for idx, chunk in enumerate(chunks):
                doc_id = f"{file.stem}_{int(last_modified)}_{idx}"
                metadata = {
                    "source": filepath_str,
                    "chunk": idx,
                    "total_chunks": len(chunks),
                    "type": file.suffix.lower().strip("."),
                    "filename": file.name
                }
                collection.add(
                    documents=[chunk],
                    ids=[doc_id],
                    metadatas=[metadata]
                )
            
            # Update file metadata
            metadata_collection.upsert(
                ids=[filepath_str],
                documents=[file.name],
                metadatas=[{"filepath": filepath_str, "last_modified": last_modified}]
            )
            
            # Update progress
            embedding_status["processed_files"] += 1
            embedding_status["progress_percentage"] = (embedding_status["processed_files"] / embedding_status["total_files"]) * 100
        
        # Mark as completed
        embedding_status["status"] = "completed"
        embedding_status["progress_percentage"] = 100
    except Exception as e:
        embedding_status["status"] = "error"
        embedding_status["error"] = str(e)
    finally:
        embedding_status["is_running"] = False

# Endpoint to get available folders
@app.get("/api/folders", response_model=FolderList)
async def get_folders():
    home_dir = Path(os.environ.get("HOME"))
    folders = []
    
    # Check standard folders
    standard_folders = [
        ("Downloads", home_dir / "Downloads"),
        ("Documents", home_dir / "Documents"),
        ("Desktop", home_dir / "Desktop")
    ]
    
    for name, path in standard_folders:
        if path.exists() and path.is_dir():
            folders.append(name)
    
    return {"folders": folders}

# Endpoint to start indexing
@app.post("/api/index")
async def start_indexing(request: IndexingRequest, background_tasks: BackgroundTasks):
    global embedding_status
    
    if embedding_status["is_running"]:
        return JSONResponse(
            status_code=400,
            content={"detail": "Indexing is already in progress"}
        )
    
    # Reset status
    embedding_status = {
        "is_running": True,
        "total_files": 0,
        "processed_files": 0,
        "current_file": "",
        "progress_percentage": 0,
        "status": "starting",
        "error": None
    }
    
    # Start indexing in the background
    background_tasks.add_task(index_files_from_folders, request.folders, request.custom_folders)
    
    return {"status": "started"}

# Endpoint to check indexing status
@app.get("/api/index/status", response_model=IndexingStatus)
async def get_indexing_status():
    return embedding_status

# Endpoint to cancel indexing
@app.post("/api/index/cancel")
async def cancel_indexing():
    global embedding_status
    
    if not embedding_status["is_running"]:
        return JSONResponse(
            status_code=400,
            content={"detail": "No indexing process is running"}
        )
    
    embedding_status["is_running"] = False
    return {"status": "cancelling"}

# Endpoint to check if collection exists
@app.get("/api/collection/exists")
async def check_collection_exists():
    try:
        # Try to get the collection
        collection = client.get_collection(
            name="my_documents",
            embedding_function=openai_ef,
        )
        # Get count of documents
        count = collection.count()
        return {"exists": True, "document_count": count}
    except Exception as e:
        return {"exists": False, "document_count": 0}

@app.get("/api/search")
async def search(query: str = Query(..., min_length=1)):
    """
    Search for documents based on a semantic query.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
    
    Returns:
        A list of search results with document content and metadata
    """
    # Check if collection exists
    if collection is None:
        return {"results": [], "error": "No documents have been indexed yet. Please index some folders first."}
        
    try:
        results = collection.query(
            query_texts=[query],
            n_results=10,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format the results for the frontend
        formatted_results = []
        all_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i] if "distances" in results else None
                similarity = 1 - distance if distance is not None else None
                
                filepath = metadata.get("source", "Unknown path")
                print("filepath", filepath)
                filename = metadata.get("filename", "Unknown filename")
                print("filename", filename)
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
                    "preview": " ".join(preview),
                    "content": content
                })
        
        return {"results": formatted_results}
    
    except Exception as e:
        return {"error": str(e), "results": []}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload= True)