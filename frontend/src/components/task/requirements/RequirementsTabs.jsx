import React from 'react';

/**
 * Component for displaying vertical tabs for different requirement categories
 */
export default function RequirementsTabs({ 
  categories, 
  activeTab, 
  onTabClick,
  requirements 
}) {
  // Helper to get count of items in a category
  const getItemCount = (categoryId) => {
    if (!requirements || !requirements[categoryId]) return 0;
    return requirements[categoryId].length;
  };
  
  return (
    <div className="h-full">
      <nav className="flex flex-col divide-y divide-gray-200" aria-label="Requirements categories">
        {categories.map((category) => {
          const isActive = activeTab === category.id;
          const itemCount = getItemCount(category.id);
          
          return (
            <button
              key={category.id}
              onClick={() => onTabClick(category.id)}
              className={`
                py-3 px-4 flex items-center justify-between text-sm transition duration-150 ease-in-out
                ${isActive 
                  ? 'bg-white text-blue-700 font-medium border-l-4 border-blue-600' 
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100 border-l-4 border-transparent'}
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              <span>{category.label}</span>
              {itemCount > 0 && (
                <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
                  isActive ? 'bg-blue-100 text-blue-600' : 'bg-gray-200 text-gray-700'
                }`}>
                  {itemCount}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
} 