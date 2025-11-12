import React from 'react';
import PropTypes from 'prop-types';
import { PlusCircle } from 'lucide-react';

const Header = ({ queryCount, onCreateClick, isLoading = false }) => {
  return (
    <div className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-soft backdrop-blur-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left section - Logo and navigation */}
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-3">
              {/* Logo/Brand */}
              <div className="w-8 h-8 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center shadow-sm">
                <span className="text-white font-bold text-sm">Q</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gradient">Query Hub</h1>
                <p className="text-xs text-gray-500 -mt-1">Task Management Dashboard</p>
              </div>
            </div>
            
            {/* Status indicator */}
            <div className="flex items-center gap-2">
              <div className={`status-indicator ${isLoading ? 'status-warning animate-pulse' : 'status-success'}`} />
              <span 
                className={`px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 ${
                  isLoading 
                    ? 'bg-warning-50 text-warning-700 border border-warning-200' 
                    : 'bg-success-50 text-success-700 border border-success-200'
                }`}
              >
                {isLoading ? 'Syncing...' : `${queryCount} Active Queries`}
              </span>
            </div>
          </div>

          {/* Right section - Actions and user menu */}
          <div className="flex items-center gap-4">
            {/* Quick search */}
            {/* <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-gray-50 rounded-xl border border-gray-200 hover:border-gray-300 transition-colors">
              <Search className="w-4 h-4 text-gray-400" />
              <input 
                type="text" 
                placeholder="Quick search..." 
                className="bg-transparent border-none outline-none text-sm text-gray-600 placeholder-gray-400 w-32 focus:w-48 transition-all duration-200"
              />
              <kbd className="hidden lg:inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-gray-500">
                ⌘K
              </kbd>
            </div> */}

            {/* Notifications */}
            {/* <button className="relative p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full border-2 border-white"></span>
            </button> */}

            {/* Create button */}
            <button 
              onClick={onCreateClick}
              className="btn btn-primary btn-md shadow-sm hover:shadow-md"
              aria-label="Create new query"
            >
              <PlusCircle className="w-4 h-4" aria-hidden="true" />
              <span className="hidden sm:inline">New Query</span>
            </button>
          </div>
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

export default Header; 