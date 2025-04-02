import React from 'react';
import { SearchResult } from '@/services/api';

interface DocumentViewerProps {
  selectedResult: SearchResult | null;
}

export default function DocumentViewer({ selectedResult }: DocumentViewerProps) {
  if (!selectedResult) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        No document selected
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto p-6">
      <div className="mb-4">
        <h2 className="text-xl font-semibold text-gray-900">{selectedResult.filename}</h2>
        <p className="text-sm text-gray-500">{selectedResult.filepath}</p>
        <div className="flex items-center mt-2">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 mr-2">
            {selectedResult.filetype}
          </span>
          <span className="text-xs text-gray-500">
            Similarity: {(selectedResult.similarity * 100).toFixed(1)}%
          </span>
        </div>
      </div>
      
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
          {selectedResult.content}
        </pre>
      </div>
    </div>
  );
}
