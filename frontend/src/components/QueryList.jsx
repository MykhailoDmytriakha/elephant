// src/components/QueryList.jsx
import React from 'react';

const QueryList = ({ queries, onCreateClick, onDetailsClick }) => {
    return (
        <div className="max-w-3xl mx-auto">
            <div className="flex justify-between items-center mb-8 px-4">
                <h1 className="text-2xl font-semibold text-gray-800">All Queries</h1>
                <button 
                    onClick={onCreateClick}
                    className="px-4 py-2 bg-blue-500 text-white rounded-md shadow-sm hover:bg-blue-600 transition-colors"
                >
                    Create New Query
                </button>
            </div>
            
            <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                {queries.map((query, index) => (
                    <div 
                        key={query.id} 
                        className={`
                            flex flex-col px-6 py-4
                            ${index !== queries.length - 1 ? 'border-b border-gray-200' : ''}
                            hover:bg-gray-50 transition-colors
                        `}
                    >
                        <div className="flex justify-between items-center mb-3">
                            <div className="flex-1">
                                <p className="text-gray-800 font-medium">
                                    {query.origin_query || 'New Query'}
                                </p>
                            </div>
                            <span className="text-sm text-gray-500 ml-4">
                                {new Date(query.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        
                        <div className="flex items-center gap-6">
                            <div className="flex-1">
                                <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                                    <div 
                                        className="h-full bg-blue-500 rounded-full"
                                        style={{ width: `${query.progress || 0}%` }}
                                    />
                                </div>
                            </div>
                            <span className="text-sm font-medium text-gray-600 min-w-[100px]">
                                {query.status || 'In Process'}
                            </span>
                            <button 
                                className="px-4 py-1.5 text-sm text-blue-500 hover:text-blue-700 hover:bg-blue-50 rounded transition-colors"
                                onClick={() => onDetailsClick(query.task_id)}
                            >
                                Details
                            </button>
                        </div>
                    </div>
                ))}
                
                {queries.length === 0 && (
                    <div className="px-6 py-8 text-center text-gray-500">
                        No Available Queries
                    </div>
                )}
            </div>
        </div>
    );
};

export default QueryList;
