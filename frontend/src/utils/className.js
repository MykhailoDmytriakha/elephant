/**
 * Utility function to combine CSS class names conditionally
 * Similar to the popular 'clsx' library but lightweight
 * 
 * @param {...(string|Array|Object|boolean|null|undefined)} classes - Classes to combine
 * @returns {string} Combined class names
 * 
 * @example
 * cn('base-class', condition && 'conditional-class', { 'object-class': true })
 * // Returns: 'base-class conditional-class object-class'
 */
export function cn(...classes) {
  const result = [];
  
  for (const cls of classes) {
    if (!cls) continue;
    
    if (typeof cls === 'string') {
      result.push(cls);
    } else if (Array.isArray(cls)) {
      const nestedResult = cn(...cls);
      if (nestedResult) result.push(nestedResult);
    } else if (typeof cls === 'object') {
      for (const [key, value] of Object.entries(cls)) {
        if (value) result.push(key);
      }
    }
  }
  
  return result.join(' ');
}

export default cn; 