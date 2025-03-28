import React from 'react';
import PropTypes from 'prop-types';
import { PlusCircle } from 'lucide-react';

const Header = ({ queryCount, onCreateClick, isLoading }) => {
  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-10 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-gray-900">Query Dashboard</h1>
            <span 
              className={`ml-3 px-2.5 py-0.5 rounded-full text-xs font-medium ${
                isLoading ? 'bg-gray-100 text-gray-500' : 'bg-blue-100 text-blue-800'
              }`}
            >
              {isLoading ? 'Loading...' : `${queryCount} Queries`}
            </span>
          </div>
          <button 
            onClick={onCreateClick}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm font-medium"
            aria-label="Create new query"
          >
            <PlusCircle className="w-5 h-5" aria-hidden="true" />
            <span>New Query</span>
          </button>
        </div>
      </div>
    </div>
  );
};

Header.propTypes = {
  queryCount: PropTypes.number.isRequired,
  onCreateClick: PropTypes.func.isRequired,
  isLoading: PropTypes.bool
};

Header.defaultProps = {
  isLoading: false
};

export default Header; 