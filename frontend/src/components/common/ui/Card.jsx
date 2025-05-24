import React from 'react';
import { cn } from '../../../utils/className';

/**
 * Card variants and their corresponding CSS classes
 */
const CARD_VARIANTS = {
  default: 'bg-white border border-gray-200',
  outlined: 'bg-white border-2 border-gray-300',
  elevated: 'bg-white shadow-lg border border-gray-100',
  primary: 'bg-blue-50 border border-blue-200',
  success: 'bg-green-50 border border-green-200',
  warning: 'bg-yellow-50 border border-yellow-200',
  danger: 'bg-red-50 border border-red-200'
};

/**
 * Card padding sizes
 */
const CARD_PADDING = {
  none: '',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
  xl: 'p-8'
};

/**
 * Reusable Card component for content containers
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Card content
 * @param {'default'|'outlined'|'elevated'|'primary'|'success'|'warning'|'danger'} props.variant - Card style variant
 * @param {'none'|'sm'|'md'|'lg'|'xl'} props.padding - Card padding size
 * @param {boolean} props.hover - Whether to add hover effects
 * @param {boolean} props.clickable - Whether the card is clickable
 * @param {string} props.className - Additional CSS classes
 * @param {Function} props.onClick - Click handler
 * @returns {React.Component} Card component
 */
export const Card = ({
  children,
  variant = 'default',
  padding = 'md',
  hover = false,
  clickable = false,
  className = '',
  onClick,
  ...props
}) => {
  const baseClasses = [
    'rounded-lg',
    'transition-all',
    'duration-200'
  ];

  const variantClasses = CARD_VARIANTS[variant] || CARD_VARIANTS.default;
  const paddingClasses = CARD_PADDING[padding] || CARD_PADDING.md;

  const interactiveClasses = [];
  if (hover || clickable || onClick) {
    interactiveClasses.push('hover:shadow-md', 'hover:-translate-y-0.5');
  }
  if (clickable || onClick) {
    interactiveClasses.push('cursor-pointer', 'active:scale-95');
  }

  const combinedClasses = cn(
    baseClasses,
    variantClasses,
    paddingClasses,
    interactiveClasses,
    className
  );

  return (
    <div
      className={combinedClasses}
      onClick={onClick}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * Card Header component
 */
export const CardHeader = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={cn('mb-4 pb-2 border-b border-gray-200', className)} 
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * Card Title component
 */
export const CardTitle = ({ children, className = '', ...props }) => {
  return (
    <h3 
      className={cn('text-lg font-semibold text-gray-900', className)} 
      {...props}
    >
      {children}
    </h3>
  );
};

/**
 * Card Content component
 */
export const CardContent = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={cn('text-gray-700', className)} 
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * Card Footer component
 */
export const CardFooter = ({ children, className = '', ...props }) => {
  return (
    <div 
      className={cn('mt-4 pt-4 border-t border-gray-200', className)} 
      {...props}
    >
      {children}
    </div>
  );
};

export default Card; 