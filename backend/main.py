import os
from pathlib import Path
import PyPDF2
from PyPDF2.errors import PdfReadError
import docx
import tiktoken
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from time import time 
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from sentence_transformers import SentenceTransformer
import torch
from sentence_transformer_embedding_function import SentenceTransformerEmbeddingFunction


start = time()

# Constants for models
OPENAI_MODEL = "text-embedding-ada-002"
SENTENCE_TRANSFORMER_MODEL = "all-mpnet-base-v2"
MODEL_MAX_TOKENS = {
    "openai": 8191,  # OpenAI's max tokens
    "sentence_transformer": 512  # MPNET's max tokens
}
BATCH_SIZE = 32  # Batch size for embeddings

def get_model_choice():
    """Get user's choice of embedding model."""
    print("\nAvailable models:")
    print(f"1. OpenAI ({OPENAI_MODEL}) - Max tokens: {MODEL_MAX_TOKENS['openai']}")
    print(f"2. Sentence Transformer ({SENTENCE_TRANSFORMER_MODEL}) - Max tokens: {MODEL_MAX_TOKENS['sentence_transformer']}")
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

def initialize_encoder(model_type):
    """Initialize and return the appropriate tokenizer."""
    if model_type == "openai":
        return tiktoken.encoding_for_model(OPENAI_MODEL)
    else:
        return None  # SentenceTransformer handles tokenization internally

def count_tokens(text: str, encoding) -> int:
    """Count tokens using the appropriate tokenizer."""
    if encoding:  # OpenAI
        return len(encoding.encode(text))
    else:  # SentenceTransformer - approximate tokens
        return len(text.split()) * 1.3  # Rough estimate of tokens

def chunk_text(text: str, encoding, model_type) -> list:
    """
    Splits text into chunks based on the model's maximum token limit.
    Each model has its own token limit defined in MODEL_MAX_TOKENS.
    """
    max_tokens = MODEL_MAX_TOKENS[model_type]
    tokens = encoding.encode(text) if encoding else len(text.split()) * 1.3
    
    if isinstance(tokens, list):
        token_count = len(tokens)
    else:
        token_count = tokens
    
    if token_count <= max_tokens:
        return [text]
    
    words = text.split()
    chunks = []
    current_chunk = ""
    current_tokens = 0
    
    for word in words:
        word_tokens = len(encoding.encode(word)) if encoding else len(word.split()) * 1.3
        if current_tokens + word_tokens > max_tokens:
            chunks.append(current_chunk.strip())
            current_chunk = word + " "
            current_tokens = word_tokens
        else:
            current_chunk += word + " "
            current_tokens += word_tokens
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            try:
                reader = PyPDF2.PdfReader(f)
                if reader.is_encrypted:
                    print(f"Skipping encrypted PDF: {file_path}")
                    return ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                return text.strip()
            except PdfReadError as e:
                print(f"Error reading PDF {file_path}: {e}")
                return ""
    except Exception as e:
        print(f"Error opening file {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text from a DOCX file using python-docx."""
    try:
        # Skip temporary files
        if file_path.name.startswith("~$"):
            print(f"Skipping temporary file: {file_path}")
            return ""
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from DOCX {file_path}: {e}")
        return ""

def extract_text_from_txt(file_path: Path) -> str:
    """Reads text from a TXT file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error extracting text from TXT {file_path}: {e}")
        return ""

def process_batch(batch_chunks, model, collection, file_path, start_idx, total_chunks, text, encoding, model_type):
    """Process a batch of chunks in parallel using ThreadPoolExecutor for embeddings."""
    if isinstance(model, SentenceTransformer):
        # SentenceTransformer can handle batches efficiently
        embeddings = model.encode(batch_chunks, show_progress_bar=False)
        for idx, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings), start=start_idx):
            doc_id = f"{file_path.stem}_chunk_{idx}"
            metadata = {
                "source": str(file_path),
                "chunk": idx,
                "total_chunks": total_chunks,
                "token_count": count_tokens(chunk, encoding),
                "type": file_path.suffix.lower().strip("."),
                "filename": file_path.stem,
                "full_text": text
            }
            collection.add(
                documents=[chunk],
                embeddings=[embedding.tolist()],
                ids=[doc_id],
                metadatas=[metadata]
            )
    else:
        # OpenAI embeddings are handled by ChromaDB
        for idx, chunk in enumerate(batch_chunks, start=start_idx):
            doc_id = f"{file_path.stem}_chunk_{idx}"
            metadata = {
                "source": str(file_path),
                "chunk": idx,
                "total_chunks": total_chunks,
                "token_count": count_tokens(chunk, encoding),
                "type": file_path.suffix.lower().strip("."),
                "filename": file_path.stem,
                "full_text": text
            }
            collection.add(
                documents=[chunk],
                ids=[doc_id],
                metadatas=[metadata]
            )

def index_files(directory: Path, collection, encoding, text_splitter, model_type, model):
    """
    Walks through all files in the specified directory, extracts text (if applicable),
    chunks the text, and adds the chunks to the provided ChromaDB collection.
    """
    futures = []
    # Use ProcessPoolExecutor for parallel processing with optimal number of workers
    max_workers = os.cpu_count() or 1  # Get number of CPU cores, fallback to 1 if None
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                file_path = Path(dirpath) / filename
                if file_path.suffix.lower() == ".pdf":
                    future = executor.submit(extract_text_from_pdf, file_path)
                elif file_path.suffix.lower() == ".docx":
                    future = executor.submit(extract_text_from_docx, file_path)
                elif file_path.suffix.lower() == ".txt":
                    future = executor.submit(extract_text_from_txt, file_path)
                else:
                    print(f"Skipping unsupported file type: {file_path.name}")
                    continue

                print(f"Processing file: {file_path.relative_to(directory)}")
                futures.append((future, file_path))

        # Process results as they complete
        for future, file_path in futures:
            text = future.result()
            if text:
                total_tokens = count_tokens(text, encoding)
                print(f"Indexing File: {file_path.name} | Total Tokens: {total_tokens}")

                # Process embeddings in parallel batches
                chunks = chunk_text(text, encoding, model_type)
                total_chunks = len(chunks)
                
                for i in range(0, total_chunks, BATCH_SIZE):
                    batch_chunks = chunks[i:i + BATCH_SIZE]
                    process_batch(batch_chunks, model, collection, file_path, i, total_chunks, text, encoding, model_type)

def main():
    # Get user's choice of embedding model
    model_type = get_model_choice()
    
    # Initialize the encoder and embedding model.
    encoding = initialize_encoder(model_type)
    model = create_model(model_type)
    print("what is model", model)
    
    # Initialize text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=MODEL_MAX_TOKENS[model_type],  # Adjust chunk size as needed.
        chunk_overlap=200,  # Overlap to preserve context.
        separators=["\n\n", "\n", " ", ""]
    )
    
    # Create or connect to the persistent ChromaDB collection.
    client = PersistentClient(path="datastore")
    collection = client.get_or_create_collection(
        name="my_documents",
        embedding_function=model
    )

    # Define the directory that contains your files.
    directory = Path(os.environ.get("HOME")) / "Downloads"/"check_folder"
    index_files(directory, collection, encoding, text_splitter, model_type, model)
    print("Indexing complete.")
    print("Time taken: ", time() - start)
    # Retrieve and print embeddings for indexed documents.
    # we can comment this .
    # results = collection.get(include=["embeddings", "metadatas"])
    # print("\nEmbeddings for indexed documents:")
    # for emb, metadata in zip(results["embeddings"], results["metadatas"]):
    #     source = metadata.get("source", "Unknown")
    #     print(f"Source: {source}")
    #     print("Embedding (first 10 elements):", emb[:10], "... (length: {})".format(len(emb)))

if __name__ == "__main__":
    main()
