import chromadb 
from chromadb import Settings
from chromadb.utils.embedding_functions.open_clip_embedding_function import OpenCLIPEmbeddingFunction
from chromadb.utils.data_loaders import ImageLoader
from PIL import Image 
from numpy import asarray
from pathlib import Path
import os 
from time import time 
import PyPDF2
import docx
import pandas as pd


embedder = OpenCLIPEmbeddingFunction()
data_loader = ImageLoader()

start = time() 

client = chromadb.PersistentClient(
    path="datastore",  # ChromaDB path
)

coll = client.get_or_create_collection(
    name="siftfiles",
    embedding_function=embedder,
    data_loader=data_loader,
)



def process_file(file_path: Path) -> tuple[str, dict]:
    """Process a file and return its content and metadata."""
    path_str = str(file_path)
    metadata = {"filepath": path_str, "type": file_path.suffix[1:]}
    
    if file_path.suffix.lower() in {'.png', '.jpg', '.jpeg'}:
        return path_str, metadata  # For images, return path
    elif file_path.suffix.lower() == '.pdf':
        try:
            with open(file_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text = ""
                for page in pdf_reader.pages[:30]:  # Limit to first 30 pages
                    text += page.extract_text()
            return text.strip(), metadata
        except Exception as e:
            raise ValueError(f"Error processing PDF {file_path}: {e}")
    elif file_path.suffix.lower() == '.docx':
        try:
            document = docx.Document(file_path)
            text = "\n".join([para.text for para in document.paragraphs])
            return text.strip(), metadata
        except Exception as e:
            raise ValueError(f"Error processing DOCX {file_path}: {e}")
    elif file_path.suffix.lower() in {'.xlsx', '.xls'}:  # Handling Excel files
        try:
            df = pd.read_excel(file_path)
            # Convert DataFrame to a CSV formatted string, you can adjust as needed.
            text = df.to_csv(index=False)
            return text.strip(), metadata
        except Exception as e:
            raise ValueError(f"Error processing Excel {file_path}: {e}")
    elif file_path.suffix.lower() == '.csv':
        try:
            # Try reading CSV with appropriate parameters.
            df = pd.read_csv(file_path, encoding="latin-1", engine='python', on_bad_lines='skip', sep=',')
            text = df.to_csv(index=False)
            return text.strip(), metadata
        except Exception as e:
            raise ValueError(f"Error processing CSV {file_path}: {e}")
    else:
        try:
            content = file_path.read_text()  # Try default (utf-8)
            return content.strip(), metadata
        except UnicodeDecodeError:
            try:
                # Fallback to a different encoding, e.g., latin-1
                content = file_path.read_text(encoding="latin-1")
                return content.strip(), metadata
            except Exception as e:
                raise ValueError(f"Cannot read file as text: {file_path}: {e}")


cur_file_id = 0
cur_img_id = 0

def parse_files(collection: chromadb.Collection, directory: Path):
    global cur_file_id, cur_img_id 

    for file in directory.iterdir():
        if file.name in {"node_modules", "venv", ".venv", "__pycache__", ".git", 'data'}:
            continue 

        if "test" in str(file).lower():
            continue 

        if "targets" in str(file).lower():
            continue

        if file.is_dir():
            # Skipping certain directories
            if file.name.lower() in {'adobe', 'nasa_adc_all_site_build', 'onedrive - personalmicrosoftsoftware.uci.edu', "high school", 'library', 'target', 'libraries', 'lib'}:
                continue

            if file.name.startswith('.'):
                continue

            print("Now in: ", str(file))
            parse_files(collection, file) 
        else:
            path = str(file)
            if file.name.startswith('.'):
                continue

            # Skip common file types and extensions
            if file.suffix[1:].lower() in {
                'exe', 'dll', 'so', 'pyc', 'pyo', 'bin',
                'zip', 'tar', 'gz', 'rar', '7z',
                'mp3', 'mp4', 'avi', 'mov',
                'db', 'sqlite', 'sqlite3'
            }:
                continue

            # Process image files
            if file.suffix[1:] in {"png", "jpg", "jpeg"}:
                try:
                    content, metadata = process_file(file)  # Process the image file
                    if content.strip():
                        image_id = f"img{cur_img_id}"
                        collection.add(images=[asarray(Image.open(path))], ids=[image_id], metadatas=[metadata])
                        cur_img_id += 1
                except Exception as e:
                    print(f"Error processing image {file.name}: {e}")
                    continue

            # Process PDF files
            elif file.suffix[1:] == "pdf":
                try:
                    content, metadata = process_file(file)  # Process the PDF file
                    if content.strip():
                        file_id = f"pdf{cur_file_id}"
                        collection.add(documents=[content], ids=[file_id], metadatas=[metadata])
                        cur_file_id += 1
                except Exception as e:
                    print(f"Error processing PDF {file.name}: {e}")
                    continue

            # Process text files
            else: 
                try:
                    content, metadata = process_file(file)  # Process the text file
                    if content.strip():
                        file_id = f"txt{cur_file_id}"
                        collection.add(documents=[content], ids=[file_id], metadatas=[metadata])
                        cur_file_id += 1
                except UnicodeDecodeError:
                    print(f"Skipping non-text file: {file.name}")
                    continue

    # global cur_file_id, cur_img_id 

    for file in directory.iterdir():
        if file.name in {"node_modules", "venv", ".venv", "__pycache__", ".git", 'data'}:
            continue 

        if "test" in str(file).lower():
            continue 

        if "targets" in str(file).lower():
            continue

        if file.is_dir():
            if file.name.lower() in {'adobe', 'nasa_adc_all_site_build', 'onedrive - personalmicrosoftsoftware.uci.edu', "high school", 'library', 'target', 'libraries', 'lib'}:
                continue

            if file.name.startswith('.'):
                continue

            print("Now in: ", str(file))
            parse_files(collection, file) 
        else:
            path = str(file)
            if file.name.startswith('.'):
                continue

            # Skip common file types and extensions
            if file.suffix[1:].lower() in {
                'exe', 'dll', 'so', 'pyc', 'pyo', 'bin',
                'zip', 'tar', 'gz', 'rar', '7z',
                'mp3', 'mp4', 'avi', 'mov',
                'db', 'sqlite', 'sqlite3'
            }:
                continue

            # Handle image files
            if file.suffix[1:] in {"png", "jpg", "jpeg"}:
                try:
                    image = Image.open(path)
                    image = asarray(image)
                    image_id = f"img{cur_img_id}"
                    image_metadata = {
                        "filepath": path,
                        "location": "local"
                    }

                    collection.add(images=[image], ids=[image_id], metadatas=[image_metadata])

                    cur_img_id += 1  
                except Exception as e:
                    print(f"Error processing image {file.name}: {e}")
                    continue

            # Handle PDF files
            elif file.suffix[1:] == "pdf":
                with open(file, 'rb') as pdf_file:
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    num_pages = len(pdf_reader.pages)
                    
                    extracted_text = ""
                    for page_num in range(min(num_pages, 30)):
                        page = pdf_reader.pages[page_num]
                        extracted_text += page.extract_text()

                file_id = f"pdf{cur_file_id}" 
                file_metadata = {
                        "filepath": path,
                        "location": "local"
                    }
                
                if extracted_text == "":
                    continue 

                collection.add(documents=[extracted_text], ids=[file_id], metadatas=[file_metadata]) 
                cur_file_id += 1 
            elif file.suffix[1:] == "docx":
                try:
                    document = docx.Document(file)
                    text = "\n".join([para.text for para in document.paragraphs])
                    return text.strip(), metadata
                except Exception as e:
                    raise ValueError(f"Error processing DOCX {file}: {e}")

            # Handle text files
            else: 
                try:
                    file_content = file.read_text()
                    file_id = f"txt{cur_file_id}"
                    file_metadata = {
                        "filepath": path,
                        "location": "local"
                    }

                    if file_content.strip() == "":
                        continue

                    collection.add(documents=[file_content], ids=[file_id], metadatas=[file_metadata])

                    cur_file_id += 1 
                except UnicodeDecodeError:
                    print(f"Skipping non-text file: {file.name}")
                    continue


print("Starting Parse")

# Default paths for documents, desktop, and downloads
# documents_dir = Path(os.environ.get("HOME")) / "Documents"
# desktop = Path(os.environ.get("HOME")) / "Desktop"
downloads = Path(os.environ.get("HOME")) / "Desktop"  # Set to Downloads

# You can choose which directory to index, for now we'll index Documents, Desktop, and Downloads
# if documents_dir.exists():
#     print("Parsing Documents directory...")
#     parse_files(coll, documents_dir)

# if desktop.exists():
#     print("Parsing Desktop directory...")
#     parse_files(coll, desktop)

if downloads.exists():
    print("Parsing Downloads directory...")
    parse_files(coll, downloads)

print("Done with file parse")

print("Time taken: ", time() - start)

# Optional: You can run a search query on the indexed files
# results = coll.query(query_texts=["What are iterators and algorithms in Python"], n_results=5)
# print(results)
