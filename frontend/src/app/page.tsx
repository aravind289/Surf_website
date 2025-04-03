'use client';

import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import SearchBar from '@/components/SearchBar';
import SearchResultsList from '@/components/SearchResultsList';
import DocumentViewer from '@/components/DocumentViewer';
import FolderSelectionModal from '@/components/FolderSelectionModal';
import EmbeddingProgressModal from '@/components/EmbeddingProgressModal';
import { 
  searchDocuments, 
  SearchResult, 
  checkCollectionExists, 
  startIndexing, 
  IndexingRequest 
} from '@/services/api';

export default function Home() {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // State for folder selection and embedding generation
  const [showFolderModal, setShowFolderModal] = useState(false);
  const [showProgressModal, setShowProgressModal] = useState(false);
  const [collectionExists, setCollectionExists] = useState(true); // Assume exists until checked

  // Check if collection exists when component mounts
  useEffect(() => {
    const checkCollection = async () => {
      try {
        const status = await checkCollectionExists();
        setCollectionExists(status.exists && status.document_count > 0);
        
        // If no collection exists, show the folder selection modal
        if (!status.exists || status.document_count === 0) {
          setShowFolderModal(true);
        }
      } catch (error) {
        console.error('Error checking collection status:', error);
        // If there's an error checking, assume we need to create embeddings
        setCollectionExists(false);
        setShowFolderModal(true);
      }
    };
    
    checkCollection();
  }, []);

  const handleSearch = async (query: string) => {
    // Handle empty query special case
    if (query === '__EMPTY_QUERY__') {
      setSearchResults([]);
      setSelectedResult(null);
      setError(null);
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await searchDocuments(query);
      
      if (response.error) {
        setError(response.error);
        setSearchResults([]);
        
        // If the error indicates no embeddings, show the folder selection modal
        if (response.error.includes('No documents have been indexed yet')) {
          setCollectionExists(false);
          setShowFolderModal(true);
        }
      } else {
        setSearchResults(response.results);
        
        // Select the first result by default
        if (response.results.length > 0) {
          setSelectedResult(response.results[0]);
        } else {
          setSelectedResult(null);
        }
      }
    } catch (err) {
      setError('An unexpected error occurred');
      setSearchResults([]);
      setSelectedResult(null);
      console.error('Search error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectResult = (result: SearchResult) => {
    setSelectedResult(result);
  };
  
  const handleStartIndexing = async (request: IndexingRequest) => {
    try {
      // Close the folder selection modal and show the progress modal
      setShowFolderModal(false);
      setShowProgressModal(true);
      
      // Start the indexing process
      await startIndexing(request);
    } catch (error) {
      console.error('Error starting indexing process:', error);
      setError('Failed to start indexing process');
      
      // If there's an error, show the folder selection modal again
      setShowProgressModal(false);
      setShowFolderModal(true);
    }
  };
  
  const handleProgressModalClose = () => {
    setShowProgressModal(false);
    setCollectionExists(true); // Assume indexing was successful
  };

  return (
    <Layout>
      <div className="flex h-full flex-col">
        <div className="flex-1 flex overflow-hidden">
          {/* Left sidebar - Search results (Mac Notes style) */}
          <div className="w-1/3 border-r border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-3 border-b border-gray-200 bg-gray-100 flex justify-between items-center">
              <h2 className="text-sm font-medium text-gray-700">Search Results</h2>
              <button 
                onClick={() => setShowFolderModal(true)}
                className="text-xs text-blue-600 hover:text-blue-800 focus:outline-none"
              >
                Manage Folders
              </button>
            </div>
            <div className="flex-1 overflow-hidden">
              {!collectionExists && searchResults.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full p-4 text-center">
                  <p className="text-gray-500 mb-4">No documents have been indexed yet.</p>
                  <button
                    onClick={() => setShowFolderModal(true)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none"
                  >
                    Select Folders to Index
                  </button>
                </div>
              ) : (
                <SearchResultsList 
                  results={searchResults}
                  selectedResultId={selectedResult?.id || null}
                  onSelectResult={handleSelectResult}
                  isLoading={isLoading}
                />
              )}
            </div>
          </div>
          
          {/* Main content area - Document viewer */}
          <div className="flex-1 flex flex-col bg-white">
            {error && !error.includes('No documents have been indexed yet') ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-red-500">{error}</div>
              </div>
            ) : !collectionExists && !selectedResult ? (
              <div className="flex flex-col items-center justify-center h-full p-4 text-center">
                <p className="text-gray-500 mb-2">Welcome to Semantic File Search</p>
                <p className="text-gray-400 text-sm mb-4">Start by selecting folders to index, then search for your documents.</p>
              </div>
            ) : (
              <DocumentViewer selectedResult={selectedResult} />
            )}
          </div>
        </div>
        
        {/* Search bar at the bottom */}
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
        
        {/* Modals */}
        <FolderSelectionModal 
          isOpen={showFolderModal} 
          onClose={() => setShowFolderModal(false)} 
          onStartIndexing={handleStartIndexing} 
        />
        
        <EmbeddingProgressModal 
          isOpen={showProgressModal} 
          onClose={handleProgressModalClose} 
        />
      </div>
    </Layout>
  );
}
