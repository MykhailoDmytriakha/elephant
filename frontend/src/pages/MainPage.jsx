import React, { useState, useEffect, useCallback, useRef } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';
import QueryList from '../components/query/QueryList';
import CreateQueryModal from '../components/query/CreateQueryModal';
import Header from '../components/layout/Header';
import Toolbar from '../components/layout/Toolbar';
import { fetchQueries } from '../utils/api';


const MainPage = () => {
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewType, setViewType] = useState('list');
  const [filterStatus, setFilterStatus] = useState('all');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [retryAttempt, setRetryAttempt] = useState(0);
  const retryAttemptRef = useRef(0);
  const navigate = useNavigate();

  const loadQueries = useCallback(async () => {
    const MAX_RETRIES = 3;
    let currentAttempt = 0; // Always start from 0 for each loadQueries call

    const attemptLoad = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await fetchQueries();
        setQueries(data);
        retryAttemptRef.current = 0; // Reset retry attempt on success
        setRetryAttempt(0); // Update UI state
        setIsLoading(false);
      } catch (err) {
        console.log(`Attempt ${currentAttempt + 1} failed:`, err.message);

        if (currentAttempt < MAX_RETRIES - 1) {
          // Retry with exponential backoff
          currentAttempt++;

          const delay = Math.min(1000 * Math.pow(2, currentAttempt - 1), 5000); // Max 5 seconds
          setTimeout(attemptLoad, delay);
        } else {
          // Max retries reached, show error in loading state
          const errorMessage = 'Unable to connect to the server. Please check if the backend is running.';
          setError(errorMessage);
          setIsLoading(false); // Keep loading false so we show error in loading div
        }
      }
    };

    attemptLoad(); // Start the first attempt
  }, []); // Remove toast dependency since we don't show toast anymore

  useEffect(() => {
    retryAttemptRef.current = 0; // Reset on component mount
    setRetryAttempt(0); // Update UI state
    loadQueries(); // Use the properly memoized function
  }, [loadQueries]); // Include loadQueries dependency

  const handleCreateClick = useCallback(() => {
    setIsModalOpen(true);
  }, []);

  const handleManualRetry = useCallback(() => {
    if (retryAttempt >= 3) {
      // Force page refresh when max retries reached
      window.location.reload();
    } else {
      retryAttemptRef.current = 0; // Reset retry count for manual retry
      setRetryAttempt(0); // Update UI state
      loadQueries();
    }
  }, [loadQueries, retryAttempt]);

  const handleDetailsClick = useCallback((taskId) => {
    navigate(`/tasks/${taskId}`);
  }, [navigate]);

  const filteredQueries = queries.filter(query => {
    const matchesSearch = query.query.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || query.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gray-25">
      <Header
        queryCount={queries.length}
        onCreateClick={handleCreateClick}
        isLoading={isLoading}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Toolbar */}
        <Toolbar
          isFilterOpen={isFilterOpen}
          setIsFilterOpen={setIsFilterOpen}
          filterStatus={filterStatus}
          setFilterStatus={setFilterStatus}
          viewType={viewType}
          setViewType={setViewType}
          onRefresh={loadQueries}
        />

        {/* Query List */}
        <QueryList
          queries={filteredQueries}
          isLoading={isLoading}
          error={error}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onDetailsClick={handleDetailsClick}
          onCreateClick={handleCreateClick}
          viewType={viewType}
          onRetry={handleManualRetry}
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