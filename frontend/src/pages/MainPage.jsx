import React, { useState, useEffect } from 'react';
import { PlusCircle, AlertCircle, RefreshCw, ChevronDown, Filter, Layout, LayoutGrid } from 'lucide-react';
import QueryList from '../components/query/QueryList';
import CreateQueryModal from '../components/query/CreateQueryModal';
import { fetchQueries } from '../utils/api';
import { useToast } from '../components/common/ToastProvider';

const MainPage = () => {
  const [queries, setQueries] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewType, setViewType] = useState('list'); // 'list' or 'grid'
  const [filterStatus, setFilterStatus] = useState('all');
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const toast = useToast();

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
      toast.showError('Failed to fetch queries. Please try again later.');
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

  const filteredQueries = queries.filter(query => {
    const matchesSearch = query.query.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || query.status.toLowerCase() === filterStatus.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 text-red-700 p-6 rounded-lg max-w-md text-center shadow-md">
          <AlertCircle className="w-8 h-8 mx-auto mb-3" />
          <h2 className="text-xl font-semibold mb-2">Error Loading Queries</h2>
          <p className="mb-4">{error}</p>
          <button 
            onClick={loadQueries}
            className="px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center justify-center gap-2 mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">Query Dashboard</h1>
              <span className="ml-3 bg-blue-100 text-blue-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
                {queries.length} Queries
              </span>
            </div>
            <button 
              onClick={handleCreateClick}
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
            >
              <PlusCircle className="w-5 h-5" />
              <span>New Query</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Toolbar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
          <div className="relative flex items-center">
            <button 
              onClick={() => setIsFilterOpen(!isFilterOpen)}
              className="mr-2 inline-flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
            >
              <Filter className="w-4 h-4" />
              <span>Filter</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {isFilterOpen && (
              <div className="absolute top-full left-0 mt-2 z-10 bg-white rounded-lg shadow-lg border border-gray-200 p-3 min-w-[200px]">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Filter by Status</h3>
                <div className="space-y-2">
                  {['all', 'pending', 'in_progress', 'completed', 'failed', 'cancelled'].map((status) => (
                    <div key={status} className="flex items-center">
                      <input
                        type="radio"
                        id={`status-${status}`}
                        name="filter-status"
                        checked={filterStatus === status}
                        onChange={() => setFilterStatus(status)}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                      />
                      <label htmlFor={`status-${status}`} className="ml-2 text-sm text-gray-700 capitalize">
                        {status === 'all' ? 'All Statuses' : status.replace('_', ' ')}
                      </label>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex border border-gray-300 rounded-lg overflow-hidden ml-2">
              <button
                onClick={() => setViewType('list')}
                className={`p-2 ${viewType === 'list' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                title="List View"
              >
                <Layout className="w-4 h-4" />
              </button>
              <button
                onClick={() => setViewType('grid')}
                className={`p-2 ${viewType === 'grid' 
                  ? 'bg-blue-100 text-blue-700' 
                  : 'bg-white text-gray-500 hover:bg-gray-50'}`}
                title="Grid View"
              >
                <LayoutGrid className="w-4 h-4" />
              </button>
            </div>
          </div>
          
          <button
            onClick={loadQueries}
            className="inline-flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-700"
            title="Refresh queries"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
        
        <QueryList
          queries={filteredQueries}
          isLoading={isLoading}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onDetailsClick={handleDetailsClick}
          viewType={viewType}
        />

        {/* Summary Information */}
        {!isLoading && filteredQueries.length > 0 && (
          <div className="mt-6 text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg">
            Showing {filteredQueries.length} out of {queries.length} queries
            {filterStatus !== 'all' && ` • Filtered by status: ${filterStatus.replace('_', ' ')}`}
            {searchTerm && ` • Search: "${searchTerm}"`}
          </div>
        )}
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