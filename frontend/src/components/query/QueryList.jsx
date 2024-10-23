import React from 'react';
import { Search } from 'lucide-react';
import StatusBadge from './StatusBadge';

const QueryList = ({ queries, isLoading, searchTerm, onSearchChange, onDetailsClick }) => {
  const filteredQueries = queries.filter(query => 
    query.query.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8">
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search queries..."
          className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* Query List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 divide-y divide-gray-200">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">
            <div className="w-6 h-6 mx-auto mb-2 border-2 border-gray-200 border-t-blue-600 rounded-full animate-spin" />
            <p>Loading queries...</p>
          </div>
        ) : filteredQueries.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            {searchTerm ? 'No queries match your search.' : 'No queries available.'}
          </div>
        ) : (
          filteredQueries.map((query) => (
            <div key={query.id} className="p-6 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {query.query}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>Task ID: {query.task_id}</span>
                    <span>Created: {new Date(query.created_at).toLocaleString()}</span>
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
                    className="px-4 py-2 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                  >
                    View Details
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default QueryList;