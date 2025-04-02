import React from 'react';
import { SearchResult } from '@/services/api';

interface SearchResultsListProps {
  results: SearchResult[];
  selectedResultId: string | null;
  onSelectResult: (result: SearchResult) => void;
  isLoading: boolean;
}

export default function SearchResultsList({ 
  results, 
  selectedResultId, 
  onSelectResult,
  isLoading
}: SearchResultsListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No results found
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      <ul className="divide-y divide-gray-200">
        {results.map((result) => (
          <li 
            key={result.id}
            className={`cursor-pointer p-3 hover:bg-gray-50 ${
              selectedResultId === result.id ? 'bg-blue-50 border-l-4 border-blue-500' : ''
            }`}
            onClick={() => onSelectResult(result)}
          >
            <div className="flex items-start">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {result.filename}
                </p>
                <p className="text-xs text-gray-500 truncate">
                  {result.filepath}
                </p>
                <p className="mt-1 text-xs text-gray-600 line-clamp-2">
                  {result.preview}
                </p>
              </div>
              <div className="ml-2 flex-shrink-0">
                <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                  {result.filetype}
                </span>
              </div>
            </div>
            <div className="mt-1">
              <span className="text-xs text-gray-500">
                Similarity: {(result.similarity * 100).toFixed(1)}%
              </span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
