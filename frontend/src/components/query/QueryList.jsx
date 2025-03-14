import React from 'react';
import { Search, Clock, AlertCircle, ArrowRight } from 'lucide-react';
import StatusBadge from './StatusBadge';

const QueryList = ({ queries, isLoading, searchTerm, onSearchChange, onDetailsClick, viewType = 'list' }) => {
  const EmptyState = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-16 h-16 flex items-center justify-center bg-gray-100 rounded-full mb-4">
        <AlertCircle className="w-8 h-8 text-gray-400" />
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">No queries found</h3>
      <p className="text-gray-500 mb-6">
        {searchTerm ? 'No queries match your search criteria.' : 'Start by creating a new query.'}
      </p>
    </div>
  );

  const LoadingState = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
      <div className="mx-auto w-12 h-12 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin mb-4" />
      <p className="text-lg text-gray-700">Loading queries...</p>
    </div>
  );

  const GridView = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {queries.map((query) => (
        <div 
          key={query.id} 
          className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
        >
          <div className="p-5 border-b border-gray-200">
            <div className="flex justify-between items-start mb-3">
              <h3 className="text-lg font-medium text-gray-900 line-clamp-2 flex-1 mr-2">
                {query.query}
              </h3>
              <StatusBadge status={query.status} />
            </div>
            <div className="text-sm text-gray-500">
              <div className="flex items-center justify-between mb-1">
                <span>Task ID: {query.task_id}</span>
                <span>{new Date(query.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <div className="flex-1">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all duration-500"
                      style={{ width: `${query.progress}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm font-medium text-gray-600 min-w-[3rem] text-right">
                  {query.progress}%
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={() => onDetailsClick?.(query.task_id)}
            className="w-full py-3 px-4 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-center gap-2 text-blue-600 font-medium"
          >
            View Details
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );

  const ListView = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-200 overflow-hidden">
      {queries.map((query) => (
        <div 
          key={query.id} 
          className="p-6 hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <h3 className="text-lg font-medium text-gray-900 mb-2 line-clamp-2">
                {query.query}
              </h3>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5" />
                  {new Date(query.created_at).toLocaleString()}
                </span>
                <span>Task ID: {query.task_id}</span>
              </div>
            </div>
            <StatusBadge status={query.status} />
          </div>
          
          <div className="mt-4">
            <div className="flex items-center gap-4">
              <div className="flex-1">
                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full transition-all duration-500"
                    style={{ width: `${query.progress}%` }}
                  />
                </div>
              </div>
              <span className="text-sm font-medium text-gray-600 min-w-[4rem]">
                {query.progress}%
              </span>
              <button 
                onClick={() => onDetailsClick?.(query.task_id)}
                className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors flex items-center gap-1.5"
              >
                View Details
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search queries..."
          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white shadow-sm"
        />
      </div>

      {/* Query List */}
      {isLoading ? (
        <LoadingState />
      ) : queries.length === 0 ? (
        <EmptyState />
      ) : (
        viewType === 'grid' ? <GridView /> : <ListView />
      )}
    </div>
  );
};

export default QueryList;