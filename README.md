# Semantic File Search

A web application for semantic file search built with Next.js, FastAPI, and Chroma DB.

## Project Structure

```
├── frontend/         # Next.js frontend application
└── backend/          # FastAPI backend application
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

4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
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

## Features

- **Semantic File Search**: Upload files and search them using natural language queries
- **Chroma DB Integration**: Utilizes Chroma DB for vector storage and semantic search capabilities
- **Modern UI**: Clean and responsive user interface built with Next.js and Tailwind CSS

## API Endpoints

- `GET /`: Check if the API is running
- `POST /upload`: Upload a file for indexing
- `GET /search?query=<search_term>`: Search for files using semantic search
