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

export interface FolderListResponse {
  folders: string[];
}

export interface IndexingRequest {
  folders: string[];
  custom_folders: string[];
}

export interface IndexingStatus {
  is_running: boolean;
  total_files: number;
  processed_files: number;
  current_file: string;
  progress_percentage: number;
  status: string;
  error?: string;
}

export interface CollectionStatus {
  exists: boolean;
  document_count: number;
}

const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

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

/**
 * Get available folders for indexing
 */
export async function getAvailableFolders(): Promise<FolderListResponse> {
  try {
    const response = await fetch(`${API_URL}/api/folders`);
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting available folders:', error);
    return { folders: [] };
  }
}

/**
 * Start indexing process for selected folders
 */
export async function startIndexing(request: IndexingRequest): Promise<{status: string}> {
  try {
    const response = await fetch(`${API_URL}/api/index`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error starting indexing process:', error);
    throw error;
  }
}

/**
 * Get current indexing status
 */
export async function getIndexingStatus(): Promise<IndexingStatus> {
  try {
    const response = await fetch(`${API_URL}/api/index/status`);
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error getting indexing status:', error);
    return {
      is_running: false,
      total_files: 0,
      processed_files: 0,
      current_file: '',
      progress_percentage: 0,
      status: 'error',
      error: error instanceof Error ? error.message : 'An unknown error occurred'
    };
  }
}

/**
 * Cancel ongoing indexing process
 */
export async function cancelIndexing(): Promise<{status: string}> {
  try {
    const response = await fetch(`${API_URL}/api/index/cancel`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error cancelling indexing process:', error);
    throw error;
  }
}

/**
 * Check if collection exists and has documents
 */
export async function checkCollectionExists(): Promise<CollectionStatus> {
  try {
    const response = await fetch(`${API_URL}/api/collection/exists`);
    
    if (!response.ok) {
      throw new Error(`Error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error checking collection status:', error);
    return { exists: false, document_count: 0 };
  }
}
