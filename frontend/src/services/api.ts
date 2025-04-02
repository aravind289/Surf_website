/**
 * API service for semantic search
 */

export interface SearchResult {
  id: string;
  filename: string;
  filepath: string;
  filetype: string;
  similarity: number;
  preview: string;
  content: string;
}

export interface SearchResponse {
  results: SearchResult[];
  error?: string;
}

const API_URL = 'http://localhost:8000';

/**
 * Search for documents based on a semantic query
 */
export async function searchDocuments(query: string, limit: number = 10): Promise<SearchResponse> {
  // Skip API call for empty queries
  if (!query || query.trim().length === 0) {
    return { results: [] };
  }
  
  try {
    const response = await fetch(`${API_URL}/api/search?query=${encodeURIComponent(query)}&limit=${limit}`);
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error searching documents:', error);
    return { 
      results: [],
      error: error instanceof Error ? error.message : 'An unknown error occurred'
    };
  }
}
