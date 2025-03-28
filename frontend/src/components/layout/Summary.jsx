import React from 'react';
import PropTypes from 'prop-types';

const Summary = ({ filteredCount, totalCount, filterStatus, searchTerm, isLoading }) => {
  if (isLoading) {
    return (
      <div 
        className="mt-6 text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg"
        role="status"
        aria-live="polite"
      >
        Loading query information...
      </div>
    );
  }

  if (filteredCount === 0) {
    return (
      <div 
        className="mt-6 text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg"
        role="status"
        aria-live="polite"
      >
        No queries found
        {filterStatus !== 'all' && ` • Filtered by status: ${filterStatus.replace('_', ' ')}`}
        {searchTerm && ` • Search: "${searchTerm}"`}
      </div>
    );
  }

  return (
    <div 
      className="mt-6 text-sm text-gray-500 px-4 py-2 bg-gray-100 rounded-lg"
      role="status"
      aria-live="polite"
    >
      Showing {filteredCount} out of {totalCount} queries
      {filterStatus !== 'all' && ` • Filtered by status: ${filterStatus.replace('_', ' ')}`}
      {searchTerm && ` • Search: "${searchTerm}"`}
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