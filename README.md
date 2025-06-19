# Semantic File Search

A web application for semantic file search built with Next.js, FastAPI, and Chroma DB. This application indexes files from your system and allows you to search them using natural language queries.

## Project Structure

```
├── frontend/         # Next.js frontend application
└── backend/          # FastAPI backend application with ChromaDB
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Index your files (by default, it indexes your Downloads folder):
   ```bash
   python main.py
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn api:app --reload
   ```
   The backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at http://localhost:3000
   Set `NEXT_PUBLIC_BACKEND_URL` in `.env.local` if your backend runs elsewhere

## Features

- **Semantic File Search**: Search your indexed files using natural language queries
- **Mac Notes-style UI**: Clean and intuitive interface inspired by the macOS Notes app
- **Automatic File Indexing**: System automatically indexes files from your Downloads folder (configurable in main.py)
- **Chroma DB Integration**: Utilizes Chroma DB for vector storage and semantic search capabilities
- **CSV and Image Support**: Indexes CSV files and images (PNG, JPG, JPEG) in addition to PDF, DOCX, and TXT formats
- **Batch Embedding Optimization**: Adds document chunks in batches for faster indexing

## API Endpoints

- `GET /api/search?query=<search_term>&limit=<number_of_results>`: Search for files using semantic search

## Usage

1. First run the backend server to ensure the API is available
2. Launch the frontend application
3. Enter your search query in the search bar at the bottom of the page
4. View search results in the left panel
5. Click on a result to view its full content in the right panel

## Deployment on Vercel

1. Install the [Vercel CLI](https://vercel.com/docs/cli) and log in
2. From the project root, run `vercel` and follow the prompts
3. Set the `NEXT_PUBLIC_BACKEND_URL` environment variable to your deployed FastAPI endpoint
4. Vercel will build the Next.js frontend and the `api/index.py` serverless function
5. After deployment, open the generated Vercel URL in your browser
