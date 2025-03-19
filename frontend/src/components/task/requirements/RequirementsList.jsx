import React from 'react';
import { RefreshCw } from 'lucide-react';

/**
 * Component for displaying a list of requirement items
 */
export default function RequirementsList({ 
  items, 
  isLoading, 
  onGenerate,
  activeCategory
}) {
  // Format category name for display (e.g., 'requirements' -> 'Requirements')
  const formatCategory = (category) => {
    return category.charAt(0).toUpperCase() + category.slice(1);
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 text-blue-500 animate-spin mb-4" />
        <p className="text-gray-500">Generating requirements...</p>
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <div className="bg-gray-50 rounded-full p-3 mb-3">
          <svg className="h-6 w-6 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-sm text-gray-500">No {formatCategory(activeCategory)} available</p>
      </div>
    );
  }

  // Format the requirement text for display - extract components in brackets if present
  const formatRequirement = (text) => {
    // Check if the text has a pattern like "[Component] description"
    const matches = text.match(/^\[([^\]]+)\]\s+(.+)$/);
    
    if (matches) {
      const component = matches[1];
      const description = matches[2];
      
      return (
        <>
          <span className="font-medium text-blue-600">[{component}]</span> {description}
        </>
      );
    }
    
    // Check if it starts with a keyword like "Tool:" or "Definition:"
    const keywordMatch = text.match(/^([^:]+):\s*(.+)$/);
    if (keywordMatch) {
      const keyword = keywordMatch[1];
      const content = keywordMatch[2];
      
      return (
        <>
          <span className="font-medium text-blue-600">{keyword}:</span> {content}
        </>
      );
    }
    
    // Return text as is if no matches
    return text;
  };

  // Get category colors based on active category
  const getCategoryColor = () => {
    const colors = {
      requirements: 'text-blue-600',
      constraints: 'text-purple-600',
      limitations: 'text-red-600',
      resources: 'text-green-600',
      tools: 'text-yellow-600',
      definitions: 'text-indigo-600'
    };
    
    return colors[activeCategory] || 'text-gray-600';
  };

  return (
    <div className="space-y-3">
      <div className="overflow-y-auto max-h-[500px] pr-1">
        <ul className="space-y-3">
          {items.map((item, index) => (
            <li 
              key={index} 
              className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm text-gray-700 break-words hyphens-auto hover:shadow transition duration-150"
            >
              {formatRequirement(item)}
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-4 text-right">
        <p className="text-sm text-gray-500">{items.length} item{items.length !== 1 ? 's' : ''}</p>
      </div>
    </div>
  );
} 