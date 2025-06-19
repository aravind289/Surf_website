'use client';

import { useState, useEffect, useCallback } from 'react';
import { getAvailableFolders, IndexingRequest } from '@/services/api';

interface FolderSelectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartIndexing: (request: IndexingRequest) => void;
}

export default function FolderSelectionModal({ isOpen, onClose, onStartIndexing }: FolderSelectionModalProps) {
  const [availableFolders, setAvailableFolders] = useState<string[]>([]);
  const [selectedFolders, setSelectedFolders] = useState<string[]>(['Downloads']);
  const [customFolders, setCustomFolders] = useState<string[]>([]);
  const [customFolderInput, setCustomFolderInput] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAvailableFolders = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getAvailableFolders();
      setAvailableFolders(response.folders);
      
      // Set Downloads as default selected if available
      if (response.folders.includes('Downloads') && selectedFolders.length === 0) {
        setSelectedFolders(['Downloads']);
      }
    } catch (error) {
      setError('Failed to load available folders');
      console.error('Error fetching folders:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchAvailableFolders();
    }
  }, [isOpen, fetchAvailableFolders]);

  const handleFolderToggle = (folder: string) => {
    if (selectedFolders.includes(folder)) {
      setSelectedFolders(selectedFolders.filter(f => f !== folder));
    } else {
      setSelectedFolders([...selectedFolders, folder]);
    }
  };

  const handleAddCustomFolder = () => {
    if (customFolderInput && !customFolders.includes(customFolderInput)) {
      setCustomFolders([...customFolders, customFolderInput]);
      setCustomFolderInput('');
    }
  };

  const handleRemoveCustomFolder = (folder: string) => {
    setCustomFolders(customFolders.filter(f => f !== folder));
  };

  const handleSubmit = () => {
    if (selectedFolders.length === 0 && customFolders.length === 0) {
      setError('Please select at least one folder to index');
      return;
    }

    const request: IndexingRequest = {
      folders: selectedFolders,
      custom_folders: customFolders
    };

    onStartIndexing(request);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex text-black items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md ">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4 text-black ">Select Folders to Index</h2>
          
          {error && (
            <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="py-4 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto"></div>
              <p className="mt-2">Loading available folders...</p>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h3 className="font-medium mb-2">Standard Folders</h3>
                <div className="space-y-2">
                  {availableFolders.map(folder => (
                    <div key={folder} className="flex items-center">
                      <input
                        type="checkbox"
                        id={`folder-${folder}`}
                        checked={selectedFolders.includes(folder)}
                        onChange={() => handleFolderToggle(folder)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                      />
                      <label htmlFor={`folder-${folder}`} className="ml-2 block text-sm text-gray-900">
                        {folder}
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-6">
                <h3 className="font-medium mb-2">Custom Folders</h3>
                <div className="flex">
                  <input
                    type="text"
                    value={customFolderInput}
                    onChange={(e) => setCustomFolderInput(e.target.value)}
                    placeholder="Enter folder path"
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                  <button
                    onClick={handleAddCustomFolder}
                    className="bg-blue-600 text-white px-3 py-2 rounded-r-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    Add
                  </button>
                </div>
                
                {customFolders.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {customFolders.map(folder => (
                      <div key={folder} className="flex items-center justify-between bg-gray-100 p-2 rounded">
                        <span className="text-sm truncate flex-1">{folder}</span>
                        <button
                          onClick={() => handleRemoveCustomFolder(folder)}
                          className="ml-2 text-red-600 hover:text-red-800"
                        >
                          Remove
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          <div className="flex justify-end space-x-3 mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </button>
            <button
              onClick={handleSubmit}
              disabled={isLoading || (selectedFolders.length === 0 && customFolders.length === 0)}
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
