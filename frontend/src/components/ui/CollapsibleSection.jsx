import React, { useState, useEffect } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

/**
 * A reusable collapsible section component with consistent styling
 * Supports both controlled and uncontrolled state
 */
const CollapsibleSection = ({ 
  title, 
  children, 
  defaultOpen = true, 
  isOpen, 
  onToggle,
  className = '',
  titleClassName = '',
  contentClassName = '',
  showChevron = true,
  disabled = false
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultOpen);

  // Allow controlled state via isOpen prop
  useEffect(() => {
    if (isOpen !== undefined) {
      setIsExpanded(isOpen);
    }
  }, [isOpen]);

  // Handle toggle with both internal and external state management
  const handleToggle = () => {
    if (disabled) return;
    
    if (isOpen === undefined) {
      // Uncontrolled mode
      setIsExpanded(!isExpanded);
    }
    
    // Call external toggle handler if provided
    if (onToggle) {
      onToggle(!isExpanded);
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 ${className}`}>
      <button 
        type="button"
        className={`flex justify-between items-center w-full p-4 border-b border-gray-200 text-left hover:bg-gray-50 transition-colors ${
          disabled ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
        } ${titleClassName}`}
        onClick={handleToggle}
        aria-expanded={isExpanded}
        disabled={disabled}
      >
        <div className="text-lg font-semibold text-gray-900">{title}</div>
        {showChevron && (
          isExpanded ? 
            <ChevronUp className="w-5 h-5 text-gray-500" /> : 
            <ChevronDown className="w-5 h-5 text-gray-500" />
        )}
      </button>
      {isExpanded && (
        <div className={`p-4 transition-all duration-200 ${contentClassName}`}>
          {children}
        </div>
      )}
    </div>
  );
};

export default CollapsibleSection; 