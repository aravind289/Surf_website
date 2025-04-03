import os
from pathlib import Path
import PyPDF2
import docx
import tiktoken
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter

def initialize_encoder(model_name="text-embedding-ada-002"):
    """Initialize and return the tiktoken encoder."""
    return tiktoken.encoding_for_model(model_name)

def count_tokens(text: str, encoding) -> int:
    """Count tokens using the provided tiktoken encoder."""
    return len(encoding.encode(text))

# def chunk_text(text: str, encoding) -> list:
    """
    Splits text into chunks such that each chunk has no more than the encoder's max token limit.
    Falls back to 8000 tokens if the encoder does not provide a model_max_length attribute.
    """
    max_tokens = getattr(encoding, "model_max_length", 8000)
    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return [text]
    
    words = text.split()
    chunks = []
    current_chunk = ""
    current_tokens = 0
    for word in words:
        word_tokens = len(encoding.encode(word))
        if current_tokens + word_tokens > max_tokens:
            chunks.append(current_chunk.strip())
            current_chunk = word + " "
            current_tokens = word_tokens
        else:
            current_chunk += word + " "
            current_tokens += word_tokens
    if current_chunk:
        chunks.append(current_chunk.strip())
    print("WHAT ARE CHUNKS", chunks)
    return chunks

def extract_text_from_pdf(file_path: Path) -> str:
    """Extracts text from a PDF file using PyPDF2."""
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from PDF {file_path}: {e}")
        return ""

def extract_text_from_docx(file_path: Path) -> str:
    """Extracts text from a DOCX file using python-docx."""
    try:
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

def index_files(directory: Path, collection, encoding, text_splitter):
    """
    Walks through all files in the specified directory, extracts text (if applicable),
    chunks the text, and adds the chunks to the provided ChromaDB collection.
    """
    for file in directory.iterdir():
        if file.suffix.lower() == ".pdf":
            text = extract_text_from_pdf(file)
        elif file.suffix.lower() == ".docx":
            text = extract_text_from_docx(file)
        elif file.suffix.lower() == ".txt":
            text = extract_text_from_txt(file)
        else:
            print(f"Skipping unsupported file type: {file.name}")
            continue

        if not text:
            continue

        total_tokens = count_tokens(text, encoding)
        print(f"Indexing File: {file.name} | Total Tokens: {total_tokens}")
        # decode tokens to understand which token id represent which word
        # can be commented. Just for debugging
        # decoded_tokens = [encoding.decode([t]) for t in tokens]
        
        # chunks = chunk_text(text, encoding)
        chunks = text_splitter.split_text(text)
        total_chunks = len(chunks)
        
        for idx, chunk in enumerate(chunks):
            chunk_tokens = count_tokens(chunk, encoding)
            print(str(file))
            print(f"  Chunk {idx+1}/{total_chunks} | Tokens: {chunk_tokens}")
            # Optionally print a preview for debugging
            # print(f"  Chunk {idx+1}/{total_chunks} | Tokens: {chunk_tokens}")
            doc_id = f"{file.stem}_chunk_{idx}"
            metadata = {
                "source": str(file),
                "chunk": idx,
                "total_chunks": total_chunks,
                "token_count": chunk_tokens,
                "type": file.suffix.lower().strip(".")
            }
            collection.add(
                documents=[chunk],
                ids=[doc_id],
                metadatas=[metadata]
            )

def main():
    # Initialize the encoder and OpenAI embedding function.
    encoding = initialize_encoder("text-embedding-ada-002")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=getattr(encoding, "model_max_length", 8000),    # Adjust chunk size as needed.
        chunk_overlap=200,  # Overlap to preserve context.
        separators=["\n\n", "\n", " ", ""]
    )
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-ada-002"
    )

    # Create or connect to the persistent ChromaDB collection.
    client = PersistentClient(path="datastore")
    collection = client.get_or_create_collection(
        name="my_documents",
        embedding_function=openai_ef
    )

    # Define the directory that contains your files.
    directory = Path(os.environ.get("HOME")) / "Downloads"
    index_files(directory, collection, encoding,text_splitter)
    print("Indexing complete.")

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
