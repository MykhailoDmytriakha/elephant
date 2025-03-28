import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import { AlertCircle, RefreshCw } from 'lucide-react';
import QueryList from '../components/query/QueryList';
import CreateQueryModal from '../components/query/CreateQueryModal';
import Header from '../components/layout/Header';
import Toolbar from '../components/layout/Toolbar';
import Summary from '../components/layout/Summary';
import { fetchQueries } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';

const ErrorDisplay = ({ error, onRetry }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="bg-red-50 text-red-700 p-6 rounded-lg max-w-md text-center shadow-md">
      <AlertCircle className="w-8 h-8 mx-auto mb-3" aria-hidden="true" />
      <h2 className="text-xl font-semibold mb-2">Error Loading Queries</h2>
      <p className="mb-4">{error}</p>
      <button 
        onClick={onRetry}
        className="px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2 mx-auto"
        aria-label="Try loading queries again"
      >
        <RefreshCw className="w-4 h-4" aria-hidden="true" />
        Try Again
      </button>
    </div>
  </div>
);

ErrorDisplay.propTypes = {
  error: PropTypes.string.isRequired,
  onRetry: PropTypes.func.isRequired
};

const MainPage = () => {
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewType, setViewType] = useState('list');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const toast = useToast();
  const navigate = useNavigate();

  const loadQueries = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchQueries();
      setQueries(data);
    } catch (err) {
      toast.showError('Failed to fetch queries. Please try again later.');
      setError('Failed to fetch queries. Please try again later.');
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    loadQueries();
  }, [loadQueries]);

  const handleCreateClick = useCallback(() => {
    setIsModalOpen(true);
  }, []);

  const handleDetailsClick = useCallback((taskId) => {
    navigate(`/tasks/${taskId}`);
  }, [navigate]);

  const filteredQueries = queries.filter(query => {
    const matchesSearch = query.query.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || query.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  if (error) {
    return <ErrorDisplay error={error} onRetry={loadQueries} />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        queryCount={queries.length} 
        onCreateClick={handleCreateClick}
        isLoading={isLoading}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Toolbar
          isFilterOpen={isFilterOpen}
          setIsFilterOpen={setIsFilterOpen}
          filterStatus={filterStatus}
          setFilterStatus={setFilterStatus}
          viewType={viewType}
          setViewType={setViewType}
          onRefresh={loadQueries}
        />
        
        <QueryList
          queries={filteredQueries}
          isLoading={isLoading}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onDetailsClick={handleDetailsClick}
          viewType={viewType}
        />

        <Summary
          filteredCount={filteredQueries.length}
          totalCount={queries.length}
          filterStatus={filterStatus}
          searchTerm={searchTerm}
          isLoading={isLoading}
        />
      </div>

      <CreateQueryModal
        isOpen={isModalOpen}
        onRequestClose={() => setIsModalOpen(false)}
        onQueryCreated={(newQuery) => {
          setQueries([newQuery, ...queries]);
          loadQueries();
        }}
      />
    </div>
  );
};

export default MainPage;