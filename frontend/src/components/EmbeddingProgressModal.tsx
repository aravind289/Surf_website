'use client';

import { useState, useEffect } from 'react';
import { getIndexingStatus, cancelIndexing, IndexingStatus } from '@/services/api';

interface EmbeddingProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function EmbeddingProgressModal({ isOpen, onClose }: EmbeddingProgressModalProps) {
  const [status, setStatus] = useState<IndexingStatus>({
    is_running: true,
    total_files: 0,
    processed_files: 0,
    current_file: '',
    progress_percentage: 0,
    status: 'starting'
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    
    const fetchStatus = async () => {
      try {
        const statusData = await getIndexingStatus();
        setStatus(statusData);
        
        // If the process is completed or has an error, we can stop polling
        if (statusData.status === 'completed' || statusData.status === 'error') {
          if (intervalId) clearInterval(intervalId);
        }
      } catch (error) {
        setError('Failed to fetch embedding status');
        console.error('Error fetching status:', error);
      }
    };
    
    if (isOpen) {
      // Immediately fetch status
      fetchStatus();
      
      // Then set up interval to fetch status every 1 second
      intervalId = setInterval(fetchStatus, 1000);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isOpen]);

  const handleCancel = async () => {
    try {
      await cancelIndexing();
      setStatus(prev => ({ ...prev, status: 'cancelling' }));
    } catch (error) {
      setError('Failed to cancel the embedding process');
      console.error('Error cancelling process:', error);
    }
  };

  const getStatusMessage = () => {
    switch (status.status) {
      case 'starting':
        return 'Starting the embedding process...';
      case 'running':
        return `Processing file ${status.processed_files} of ${status.total_files}`;
      case 'cancelling':
        return 'Cancelling the embedding process...';
      case 'cancelled':
        return 'Embedding process was cancelled.';
      case 'completed':
        return 'Embedding process completed successfully!';
      case 'error':
        return `Error: ${status.error || 'Unknown error occurred'}`;
      default:
        return 'Processing...';
    }
  };

  const canClose = ['completed', 'cancelled', 'error'].includes(status.status);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Generating Embeddings</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}

          <div className="mb-4">
            <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
              <div 
                className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-in-out"
                style={{ width: `${status.progress_percentage}%` }}
              ></div>
            </div>
            <div className="flex justify-between mt-1 text-sm text-gray-600">
              <span>{Math.round(status.progress_percentage)}%</span>
              <span>{status.processed_files} / {status.total_files} files</span>
            </div>
          </div>

          <div className="mb-6">
            <p className="text-center">{getStatusMessage()}</p>
            {status.current_file && status.status === 'running' && (
              <p className="text-center text-sm text-gray-500 mt-1 truncate">
                Current file: {status.current_file}
              </p>
            )}
          </div>

          <div className="flex justify-end space-x-3">
            {status.is_running && (
              <button
                onClick={handleCancel}
                className="px-4 py-2 border border-red-300 text-red-600 rounded-md hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Cancel
              </button>
            )}
            <button
              onClick={onClose}
              disabled={!canClose}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {canClose ? 'Close' : 'Please wait...'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
