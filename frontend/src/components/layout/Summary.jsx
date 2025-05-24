import React from 'react';
import { BarChart3, Clock, CheckCircle2, AlertTriangle, TrendingUp, Filter } from 'lucide-react';
import PropTypes from 'prop-types';

const Summary = ({ filteredCount, totalCount, filterStatus, searchTerm, isLoading }) => {
  // Calculate some mock statistics - in a real app, these would come from the API
  const completedCount = Math.floor(totalCount * 0.6);
  const inProgressCount = Math.floor(totalCount * 0.25);
  const failedCount = totalCount - completedCount - inProgressCount;
  const avgProgress = Math.floor((Math.random() * 30) + 70); // Mock average progress

  const stats = [
    {
      label: 'Total Queries',
      value: totalCount,
      icon: BarChart3,
      className: 'bg-primary-50 text-primary-700 border-primary-200',
      change: '+12%',
      changeType: 'positive'
    },
    {
      label: 'Completed',
      value: completedCount,
      icon: CheckCircle2,
      className: 'bg-success-50 text-success-700 border-success-200',
      change: '+8%',
      changeType: 'positive'
    },
    {
      label: 'In Progress',
      value: inProgressCount,
      icon: Clock,
      className: 'bg-warning-50 text-warning-700 border-warning-200',
      change: '+3%',
      changeType: 'positive'
    },
    {
      label: 'Failed',
      value: failedCount,
      icon: AlertTriangle,
      className: 'bg-danger-50 text-danger-700 border-danger-200',
      change: '-2%',
      changeType: 'negative'
    }
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {Array.from({ length: 4 }, (_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="flex items-center justify-between mb-4">
              <div className="skeleton w-12 h-12 rounded-xl" />
              <div className="skeleton w-16 h-6 rounded-full" />
            </div>
            <div className="skeleton w-20 h-8 mb-2" />
            <div className="skeleton w-24 h-4" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div 
            key={stat.label}
            className="card card-hover p-6 animate-slide-up"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            <div className="flex items-center justify-between mb-4">
              <div className={`p-3 rounded-xl border ${stat.className}`}>
                <stat.icon className="w-6 h-6" />
              </div>
              <div className={`text-xs font-medium px-2 py-1 rounded-full ${
                stat.changeType === 'positive' 
                  ? 'bg-success-50 text-success-700' 
                  : 'bg-danger-50 text-danger-700'
              }`}>
                {stat.change}
              </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">
              {stat.value.toLocaleString()}
            </div>
            <div className="text-sm font-medium text-gray-600">
              {stat.label}
            </div>
          </div>
        ))}
      </div>

      {/* Quick Insights */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Average Progress Card */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Average Progress</h3>
            <TrendingUp className="w-5 h-5 text-primary-600" />
          </div>
          <div className="flex items-end gap-4">
            <div className="text-3xl font-bold text-gray-900">{avgProgress}%</div>
            <div className="flex-1">
              <div className="progress-bar mb-2">
                <div 
                  className="progress-fill"
                  style={{ width: `${avgProgress}%` }}
                />
              </div>
              <div className="text-sm text-gray-600">
                Across all active queries
              </div>
            </div>
          </div>
        </div>

        {/* Current Filter Status */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Current View</h3>
            <Filter className="w-5 h-5 text-primary-600" />
          </div>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-600">Showing:</span>
              <span className="text-sm font-semibold text-gray-900">
                {filteredCount} of {totalCount} queries
              </span>
            </div>
            {filterStatus !== 'all' && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Status Filter:</span>
                <span className="badge badge-info text-xs">
                  {filterStatus.replace('_', ' ')}
                </span>
              </div>
            )}
            {searchTerm && (
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-600">Search:</span>
                <span className="text-sm font-mono text-gray-900 bg-gray-100 px-2 py-1 rounded">
                  "{searchTerm}"
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Performance Indicator */}
      {totalCount > 0 && (
        <div className="card p-6 bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-1">
                Performance Overview
              </h3>
              <p className="text-sm text-gray-600">
                {completedCount > inProgressCount + failedCount 
                  ? "Great job! Most of your queries are completed successfully." 
                  : "You have several queries in progress. Keep up the momentum!"}
              </p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-primary-700">
                {Math.round((completedCount / totalCount) * 100)}%
              </div>
              <div className="text-sm font-medium text-primary-600">
                Success Rate
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

Summary.propTypes = {
  filteredCount: PropTypes.number.isRequired,
  totalCount: PropTypes.number.isRequired,
  filterStatus: PropTypes.string.isRequired,
  searchTerm: PropTypes.string,
  isLoading: PropTypes.bool
};

Summary.defaultProps = {
  searchTerm: '',
  isLoading: false
};

export default Summary; 