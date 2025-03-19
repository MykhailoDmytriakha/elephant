import React, { useState } from 'react';
import { RefreshCw, ChevronRight, ArrowLeft } from 'lucide-react';
import { CollapsibleSection } from '../TaskComponents';
import RequirementsList from './RequirementsList';

/**
 * Component for displaying and generating task requirements with card-based navigation
 */
export default function TaskRequirements({ 
  requirements,
  isGeneratingRequirements,
  onGenerateRequirements,
  taskState
}) {
  // State for tracking the active category
  const [activeCategory, setActiveCategory] = useState(null);
  
  // Categories of requirements and their display names
  const categories = [
    { id: 'requirements', label: 'Requirements' },
    { id: 'constraints', label: 'Constraints' },
    { id: 'limitations', label: 'Limitations' },
    { id: 'resources', label: 'Resources' },
    { id: 'tools', label: 'Tools' },
    { id: 'definitions', label: 'Definitions' }
  ];
  
  // Format category name for display (e.g., 'requirements' -> 'Requirements')
  const formatCategory = (category) => {
    return category.charAt(0).toUpperCase() + category.slice(1);
  };
  
  // Helper to get items for a specific category
  const getCategoryItems = (categoryId) => {
    if (!requirements) return [];
    return requirements[categoryId] || [];
  };
  
  // Get the items for the active category
  const getActiveItems = () => {
    if (!activeCategory) return [];
    return getCategoryItems(activeCategory);
  };
  
  // Check if any requirements exist
  const hasRequirements = requirements && Object.keys(requirements).some(key => 
    Array.isArray(requirements[key]) && requirements[key].length > 0
  );
  
  // Handle card click
  const handleCardClick = (categoryId) => {
    setActiveCategory(categoryId);
  };
  
  // Handle back button click
  const handleBackClick = () => {
    setActiveCategory(null);
  };
  
  // Helper to get category background color
  const getCategoryColor = (categoryId) => {
    const colors = {
      requirements: 'bg-blue-50 border-blue-200 text-blue-700',
      constraints: 'bg-purple-50 border-purple-200 text-purple-700',
      limitations: 'bg-red-50 border-red-200 text-red-700',
      resources: 'bg-green-50 border-green-200 text-green-700',
      tools: 'bg-yellow-50 border-yellow-200 text-yellow-700',
      definitions: 'bg-indigo-50 border-indigo-200 text-indigo-700'
    };
    
    return colors[categoryId] || 'bg-gray-50 border-gray-200 text-gray-700';
  };
  
  // Helper to get category badge color
  const getBadgeColor = (categoryId) => {
    const colors = {
      requirements: 'bg-blue-100 text-blue-800',
      constraints: 'bg-purple-100 text-purple-800',
      limitations: 'bg-red-100 text-red-800',
      resources: 'bg-green-100 text-green-800',
      tools: 'bg-yellow-100 text-yellow-800',
      definitions: 'bg-indigo-100 text-indigo-800'
    };
    
    return colors[categoryId] || 'bg-gray-100 text-gray-800';
  };
  
  // Render a grid of category cards
  const renderCategoryCards = () => {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map((category) => {
          const items = getCategoryItems(category.id);
          const hasItems = items.length > 0;
          
          return (
            <button
              key={category.id}
              onClick={() => handleCardClick(category.id)}
              disabled={!hasItems}
              className={`
                p-6 rounded-lg border shadow-sm transition duration-150
                ${hasItems 
                  ? `${getCategoryColor(category.id)} hover:shadow-md cursor-pointer` 
                  : 'bg-gray-50 border-gray-200 text-gray-400 opacity-60 cursor-not-allowed'}
              `}
            >
              <div className="flex flex-col items-center text-center">
                <h3 className="text-lg font-medium mb-2">{category.label}</h3>
                {hasItems ? (
                  <>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${getBadgeColor(category.id)}`}>
                      {items.length} item{items.length !== 1 ? 's' : ''}
                    </span>
                    <p className="mt-2 text-sm">Click to view details</p>
                  </>
                ) : (
                  <p className="text-sm">No items available</p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    );
  };
  
  // Render the detailed category view
  const renderCategoryView = () => {
    if (!activeCategory) return null;
    
    return (
      <div className="space-y-4">
        <div className="flex items-center">
          <button
            onClick={handleBackClick}
            className="mr-3 p-1 rounded-full hover:bg-gray-100 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center">
            <span className="text-gray-500">Categories</span>
            <ChevronRight className="w-4 h-4 mx-2 text-gray-400" />
            <span className={`font-medium text-lg ${getCategoryColor(activeCategory).split(' ').pop()}`}>
              {formatCategory(activeCategory)}
            </span>
          </div>
        </div>
        
        <RequirementsList 
          items={getActiveItems()}
          isLoading={isGeneratingRequirements}
          onGenerate={onGenerateRequirements}
          activeCategory={activeCategory}
        />
      </div>
    );
  };
  
  return (
    <CollapsibleSection title="Requirements" defaultOpen={true}>
      {hasRequirements ? (
        <div className="space-y-6">
          {/* Content area showing either cards or detailed list */}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden p-6">
            {activeCategory ? renderCategoryView() : renderCategoryCards()}
          </div>
          
          {/* Action buttons */}
          <div className="flex justify-end">
            <button
              onClick={onGenerateRequirements}
              disabled={isGeneratingRequirements}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <RefreshCw className={`w-4 h-4 ${isGeneratingRequirements ? 'animate-spin' : ''}`} />
              Regenerate Requirements
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 px-4 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="max-w-md text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2z" />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-gray-900">No requirements defined</h3>
            <p className="mt-1 text-sm text-gray-500">
              Generate requirements to help define the technical specifications of your task.
            </p>
            <div className="mt-6">
              <button
                onClick={onGenerateRequirements}
                disabled={isGeneratingRequirements}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isGeneratingRequirements ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>Generate Requirements</>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </CollapsibleSection>
  );
} 