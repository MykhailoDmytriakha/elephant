import React, { forwardRef } from 'react';
import { cn } from '../../../utils/className';

/**
 * Input variants and their corresponding CSS classes
 */
const INPUT_VARIANTS = {
  default: 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
  error: 'border-red-300 focus:border-red-500 focus:ring-red-500 text-red-900',
  success: 'border-green-300 focus:border-green-500 focus:ring-green-500',
  disabled: 'border-gray-200 bg-gray-50 text-gray-500 cursor-not-allowed'
};

/**
 * Input sizes and their corresponding CSS classes
 */
const INPUT_SIZES = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-3 py-2 text-base',
  lg: 'px-4 py-3 text-lg'
};

/**
 * Reusable Input component with validation states and consistent styling
 * 
 * @param {Object} props - Component props
 * @param {string} props.label - Input label
 * @param {string} props.placeholder - Input placeholder
 * @param {string} props.value - Input value
 * @param {Function} props.onChange - Change handler
 * @param {'default'|'error'|'success'|'disabled'} props.variant - Input style variant
 * @param {'sm'|'md'|'lg'} props.size - Input size
 * @param {boolean} props.disabled - Whether the input is disabled
 * @param {boolean} props.required - Whether the input is required
 * @param {boolean} props.fullWidth - Whether the input should take full width
 * @param {string} props.error - Error message to display
 * @param {string} props.helperText - Helper text to display
 * @param {string} props.className - Additional CSS classes
 * @param {'text'|'email'|'password'|'number'|'tel'|'url'} props.type - Input type
 * @param {React.Ref} ref - Forwarded ref
 * @returns {React.Component} Input component
 */
export const Input = forwardRef(({
  label,
  placeholder,
  value,
  onChange,
  variant = 'default',
  size = 'md',
  disabled = false,
  required = false,
  fullWidth = false,
  error,
  helperText,
  className = '',
  type = 'text',
  ...props
}, ref) => {
  const baseClasses = [
    'block',
    'rounded-md',
    'border',
    'shadow-sm',
    'transition-colors',
    'duration-200',
    'focus:outline-none',
    'focus:ring-1'
  ];

  // Determine variant based on error state
  const effectiveVariant = error ? 'error' : disabled ? 'disabled' : variant;
  const variantClasses = INPUT_VARIANTS[effectiveVariant] || INPUT_VARIANTS.default;
  const sizeClasses = INPUT_SIZES[size] || INPUT_SIZES.md;
  const widthClasses = fullWidth ? 'w-full' : '';

  const inputClasses = cn(
    baseClasses,
    variantClasses,
    sizeClasses,
    widthClasses,
    className
  );

  return (
    <div className={fullWidth ? 'w-full' : ''}>
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      
      <input
        ref={ref}
        type={type}
        className={inputClasses}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        disabled={disabled}
        required={required}
        {...props}
      />
      
      {(error || helperText) && (
        <div className="mt-1">
          {error && (
            <p className="text-sm text-red-600">
              {error}
            </p>
          )}
          {!error && helperText && (
            <p className="text-sm text-gray-500">
              {helperText}
            </p>
          )}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 