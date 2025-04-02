'use client';

import { useState, useEffect } from 'react';
import Layout from '@/components/Layout';
import SearchBar from '@/components/SearchBar';
import SearchResultsList from '@/components/SearchResultsList';
import DocumentViewer from '@/components/DocumentViewer';
import { searchDocuments, SearchResult } from '@/services/api';

export default function Home() {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  return (
    <Layout>
      <div className="flex h-full flex-col">
        <div className="flex-1 flex overflow-hidden">
          {/* Left sidebar - Search results (Mac Notes style) */}
          <div className="w-1/3 border-r border-gray-200 bg-gray-50 flex flex-col">
            <div className="p-3 border-b border-gray-200 bg-gray-100">
              <h2 className="text-sm font-medium text-gray-700">Search Results</h2>
            </div>
            <div className="flex-1 overflow-hidden">
              <SearchResultsList 
                results={searchResults}
                selectedResultId={selectedResult?.id || null}
                onSelectResult={handleSelectResult}
                isLoading={isLoading}
              />
            </div>
          </div>
          
          {/* Main content area - Document viewer */}
          <div className="flex-1 flex flex-col bg-white">
            {error ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-red-500">{error}</div>
              </div>
            ) : (
              <DocumentViewer selectedResult={selectedResult} />
            )}
          </div>
        </div>
        
        {/* Search bar at the bottom */}
        <SearchBar onSearch={handleSearch} isLoading={isLoading} />
      </div>
    </Layout>
  );
}
