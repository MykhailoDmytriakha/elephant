import React, { useState, useEffect } from 'react';
import { PlusCircle, AlertCircle } from 'lucide-react';
import QueryList from '../components/QueryList';
import CreateQueryModal from '../components/CreateQueryModal';
import { fetchQueries } from '../utils/api';

const MainPage = () => {
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadQueries();
  }, []);

  const loadQueries = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchQueries();
      setQueries(data);
    } catch (err) {
      setError('Failed to fetch queries. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateClick = () => {
    setIsModalOpen(true);
  };

  const handleDetailsClick = (taskId) => {
    // Navigate to details page
    window.location.href = `/tasks/${taskId}`;
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 text-red-700 p-4 rounded-lg max-w-md text-center">
          <AlertCircle className="w-6 h-6 mx-auto mb-2" />
          <p>{error}</p>
          <button 
            onClick={loadQueries}
            className="mt-4 px-4 py-2 bg-red-100 rounded-lg hover:bg-red-200 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <h1 className="text-2xl font-bold text-gray-900">Query Dashboard</h1>
            <button 
              onClick={handleCreateClick}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <PlusCircle className="w-5 h-5" />
              <span>New Query</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <QueryList
          queries={queries}
          isLoading={isLoading}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onDetailsClick={handleDetailsClick}
        />
      </div>

      <CreateQueryModal
        isOpen={isModalOpen}
        onRequestClose={() => setIsModalOpen(false)}
        onQueryCreated={(newQuery) => {
          setQueries([newQuery, ...queries]);
          loadQueries(); // Reload all queries to ensure consistency
        }}
      />
    </div>
  );
};

export default MainPage;