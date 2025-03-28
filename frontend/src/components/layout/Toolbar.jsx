import React, { useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { Filter, Layout, LayoutGrid, ChevronDown, RefreshCw } from 'lucide-react';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All Statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' }
];

const Toolbar = ({ 
  isFilterOpen, 
  setIsFilterOpen, 
  filterStatus, 
  setFilterStatus, 
  viewType, 
  setViewType, 
  onRefresh 
}) => {
  const filterRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (filterRef.current && !filterRef.current.contains(event.target)) {
        setIsFilterOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [setIsFilterOpen]);

  const handleKeyDown = (event) => {
    if (event.key === 'Escape') {
      setIsFilterOpen(false);
    }
  };

  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
      <div className="relative flex items-center" ref={filterRef}>
        <button 
          onClick={() => setIsFilterOpen(!isFilterOpen)}
          className="mr-2 inline-flex items-center gap-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium"
          aria-expanded={isFilterOpen}
          aria-haspopup="true"
          aria-label="Filter queries by status"
        >
          <Filter className="w-4 h-4" aria-hidden="true" />
          <span>Filter</span>
          <ChevronDown className="w-4 h-4" aria-hidden="true" />
        </button>
        
        {isFilterOpen && (
          <div 
            className="absolute top-full left-0 mt-2 z-10 bg-white rounded-lg shadow-lg border border-gray-200 p-3 min-w-[200px]"
            role="menu"
            aria-orientation="vertical"
            aria-labelledby="filter-menu"
            onKeyDown={handleKeyDown}
          >
            <h3 className="text-sm font-medium text-gray-700 mb-2" id="filter-menu">Filter by Status</h3>
            <div className="space-y-2">
              {STATUS_OPTIONS.map(({ value, label }) => (
                <div key={value} className="flex items-center">
                  <input
                    type="radio"
                    id={`status-${value}`}
                    name="filter-status"
                    checked={filterStatus === value}
                    onChange={() => setFilterStatus(value)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500"
                    role="menuitemradio"
                    aria-checked={filterStatus === value}
                  />
                  <label 
                    htmlFor={`status-${value}`} 
                    className="ml-2 text-sm text-gray-700 capitalize"
                    role="menuitem"
                  >
                    {label}
                  </label>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <div className="flex border border-gray-300 rounded-lg overflow-hidden ml-2" role="group" aria-label="View type">
          <button
            onClick={() => setViewType('list')}
            className={`p-2 ${viewType === 'list' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-white text-gray-500 hover:bg-gray-50'}`}
            title="List View"
            aria-pressed={viewType === 'list'}
          >
            <Layout className="w-4 h-4" aria-hidden="true" />
          </button>
          <button
            onClick={() => setViewType('grid')}
            className={`p-2 ${viewType === 'grid' 
              ? 'bg-blue-100 text-blue-700' 
              : 'bg-white text-gray-500 hover:bg-gray-50'}`}
            title="Grid View"
            aria-pressed={viewType === 'grid'}
          >
            <LayoutGrid className="w-4 h-4" aria-hidden="true" />
          </button>
        </div>
      </div>
      
      <button
        onClick={onRefresh}
        className="inline-flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm text-gray-700"
        title="Refresh queries"
        aria-label="Refresh queries"
      >
        <RefreshCw className="w-4 h-4" aria-hidden="true" />
        <span>Refresh</span>
      </button>
    </div>
  );
};

Toolbar.propTypes = {
  isFilterOpen: PropTypes.bool.isRequired,
  setIsFilterOpen: PropTypes.func.isRequired,
  filterStatus: PropTypes.string.isRequired,
  setFilterStatus: PropTypes.func.isRequired,
  viewType: PropTypes.oneOf(['list', 'grid']).isRequired,
  setViewType: PropTypes.func.isRequired,
  onRefresh: PropTypes.func.isRequired
};

export default Toolbar; 