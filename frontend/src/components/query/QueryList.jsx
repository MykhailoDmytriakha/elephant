import React from 'react';
import { Search, Clock, AlertCircle, ArrowRight, Calendar, Hash, TrendingUp, Eye } from 'lucide-react';
import StatusBadge from './StatusBadge';

const QueryList = ({ queries, isLoading, searchTerm, onSearchChange, onDetailsClick, viewType = 'list' }) => {
  const EmptyState = () => (
    <div className="card p-12 text-center animate-fade-in">
      <div className="mx-auto w-20 h-20 flex items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 rounded-2xl mb-6">
        <AlertCircle className="w-10 h-10 text-gray-400" />
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-3">No queries found</h3>
      <p className="text-gray-600 mb-8 max-w-sm mx-auto leading-relaxed">
        {searchTerm 
          ? `No queries match "${searchTerm}". Try adjusting your search terms.` 
          : 'Start by creating your first query to manage and track your tasks.'
        }
      </p>
      {!searchTerm && (
        <button className="btn btn-primary btn-lg">
          <ArrowRight className="w-5 h-5" />
          Create Your First Query
        </button>
      )}
    </div>
  );

  const LoadingState = () => (
    <div className="card p-12 text-center">
      <div className="mx-auto w-16 h-16 spinner mb-6" />
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Loading queries...</h3>
      <p className="text-gray-600">Fetching your latest data</p>
    </div>
  );

  const SkeletonCard = () => (
    <div className="card p-6 animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="skeleton h-6 w-3/4 mb-3" />
          <div className="skeleton h-4 w-1/2" />
        </div>
        <div className="skeleton h-8 w-24 rounded-full" />
      </div>
      <div className="flex items-center gap-4 mt-4">
        <div className="skeleton h-2 flex-1 rounded-full" />
        <div className="skeleton h-8 w-24" />
      </div>
    </div>
  );

  const GridView = () => (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      {isLoading ? (
        Array.from({ length: 8 }, (_, i) => <SkeletonCard key={i} />)
      ) : (
        queries.map((query) => (
          <div 
            key={query.id} 
            className="card card-hover animate-slide-up group"
            style={{ animationDelay: `${Math.min(queries.indexOf(query) * 50, 500)}ms` }}
          >
            <div className="p-6">
              {/* Header */}
              <div className="flex justify-between items-start mb-5">
                <div className="flex-1 min-w-0 pr-3">
                  <div className="mb-3">
                    <h3 className="text-lg font-light text-gray-900 leading-snug line-clamp-3 group-hover:text-primary-700 transition-colors duration-200">
                      {query.query}
                    </h3>
                    {/* Add a subtle gradient line under the title */}
                    <div className="h-0.5 w-8 bg-gradient-to-r from-primary-500 to-primary-300 mt-2 opacity-60"></div>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <div className="flex items-center gap-1 bg-gray-50 px-2 py-1 rounded-md">
                      <Hash className="w-3 h-3" />
                      <span className="font-mono font-medium">{query.task_id}</span>
                    </div>
                  </div>
                </div>
                <div className="flex-shrink-0">
                  <StatusBadge status={query.status} size="sm" showPulse={query.status === 'in_progress'} />
                </div>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-4 text-xs text-gray-500 mb-6">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  <span>{new Date(query.created_at).toLocaleDateString()}</span>
                </div>
                <div className="flex items-center gap-1">
                  <TrendingUp className="w-3 h-3" />
                  <span className="font-medium">{query.progress}%</span>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-gray-600">Progress</span>
                  <span className="text-xs font-light text-gray-900">{query.progress}%</span>
                </div>
                <div className="progress-bar">
                  <div
                    className="progress-fill"
                    style={{ width: `${query.progress}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Action footer */}
            <div className="border-t border-gray-100 bg-gray-25 px-6 py-4">
              <button 
                onClick={() => onDetailsClick?.(query.task_id)}
                className="btn btn-secondary btn-sm w-full justify-center group"
              >
                <Eye className="w-4 h-4 group-hover:scale-110 transition-transform" />
                View Details
                <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );

  const ListView = () => (
    <div className="space-y-4">
      {isLoading ? (
        Array.from({ length: 5 }, (_, i) => <SkeletonCard key={i} />)
      ) : (
        queries.map((query, index) => (
          <div 
            key={query.id} 
            className="card card-hover p-6 animate-slide-up group"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between gap-6">
              {/* Main content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1 min-w-0 pr-4">
                    <h3 className="text-2xl font-light text-gray-900 leading-tight line-clamp-2 group-hover:text-primary-700 transition-colors duration-200 mb-2">
                      {query.query}
                    </h3>
                    {/* Enhanced subtitle with gradient line */}
                    <div className="h-1 w-12 bg-gradient-to-r from-primary-500 to-primary-300 rounded-full opacity-70 mb-3"></div>
                  </div>
                  <div className="flex-shrink-0">
                    <StatusBadge 
                      status={query.status} 
                      size="md" 
                      showPulse={query.status === 'in_progress'}
                    />
                  </div>
                </div>
                
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-6">
                  <div className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                    <Clock className="w-4 h-4" />
                    <span className="font-medium">{new Date(query.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex items-center gap-1.5 bg-gray-50 px-3 py-1.5 rounded-lg">
                    <Hash className="w-4 h-4" />
                    <span className="font-mono font-medium">{query.task_id}</span>
                  </div>
                </div>
                
                {/* Progress section */}
                <div className="flex items-center gap-6">
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-gray-700">Progress</span>
                      <span className="text-lg font-light text-gray-900">{query.progress}%</span>
                    </div>
                    <div className="progress-bar h-3">
                      <div
                        className="progress-fill"
                        style={{ width: `${query.progress}%` }}
                      />
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => onDetailsClick?.(query.task_id)}
                    className="btn btn-primary btn-md group flex-shrink-0"
                  >
                    <Eye className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    View Details
                    <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );

  return (
    <div className="space-y-8">
      {/* Enhanced Search Bar */}
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-gray-400" />
        </div>
        <input
          type="text"
          value={searchTerm}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search queries, task IDs, or descriptions..."
          className="input pl-12 pr-16 py-4 text-base shadow-sm hover:shadow-md focus:shadow-lg transition-all duration-200"
        />
        {searchTerm && (
          <button
            onClick={() => onSearchChange('')}
            className="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-400 hover:text-gray-600"
          >
            <span className="text-sm">Clear</span>
          </button>
        )}
      </div>

      {/* Results */}
      {isLoading ? (
        <LoadingState />
      ) : queries.length === 0 ? (
        <EmptyState />
      ) : (
        <>
          {/* Results header */}
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              {searchTerm ? (
                <>Showing <span className="font-semibold">{queries.length}</span> results for "<span className="font-semibold">{searchTerm}</span>"</>
              ) : (
                <>Showing <span className="font-semibold">{queries.length}</span> queries</>
              )}
            </div>
          </div>
          
          {/* Query List */}
          {viewType === 'grid' ? <GridView /> : <ListView />}
        </>
      )}
    </div>
  );
};

export default QueryList;