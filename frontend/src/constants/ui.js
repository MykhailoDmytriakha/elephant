/**
 * UI Constants
 * 
 * Centralized constants for UI elements to avoid magic strings and numbers.
 * Provides consistency across components and easier maintenance.
 */

// ============================================================================
// ANIMATION CONSTANTS
// ============================================================================
export const ANIMATION = {
  DURATION: {
    FAST: 150,
    NORMAL: 200,
    SLOW: 300,
    EXTRA_SLOW: 500
  },
  EASING: {
    EASE_IN: 'ease-in',
    EASE_OUT: 'ease-out',
    EASE_IN_OUT: 'ease-in-out',
    LINEAR: 'linear'
  }
};

// ============================================================================
// SIZING CONSTANTS
// ============================================================================
export const SIZE = {
  EXTRA_SMALL: 'xs',
  SMALL: 'sm',
  MEDIUM: 'md',
  LARGE: 'lg',
  EXTRA_LARGE: 'xl'
};

// ============================================================================
// SPACING CONSTANTS
// ============================================================================
export const SPACING = {
  NONE: 0,
  XS: 4,
  SM: 8,
  MD: 16,
  LG: 24,
  XL: 32,
  XXL: 48
};

// ============================================================================
// BREAKPOINT CONSTANTS
// ============================================================================
export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  XXL: 1536
};

// ============================================================================
// Z-INDEX CONSTANTS
// ============================================================================
export const Z_INDEX = {
  BASE: 0,
  DROPDOWN: 1000,
  STICKY: 1020,
  FIXED: 1030,
  MODAL_BACKDROP: 1040,
  MODAL: 1050,
  POPOVER: 1060,
  TOOLTIP: 1070,
  TOAST: 1080,
  OVERLAY: 9999
};

// ============================================================================
// STATUS CONSTANTS
// ============================================================================
export const STATUS = {
  PENDING: 'pending',
  IN_PROGRESS: 'in-progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
  BLOCKED: 'blocked',
  READY_FOR_VALIDATION: 'ready-for-validation'
};

// ============================================================================
// VARIANT CONSTANTS
// ============================================================================
export const VARIANT = {
  PRIMARY: 'primary',
  SECONDARY: 'secondary',
  SUCCESS: 'success',
  DANGER: 'danger',
  WARNING: 'warning',
  INFO: 'info',
  OUTLINE: 'outline',
  GHOST: 'ghost',
  LINK: 'link'
};

// ============================================================================
// MESSAGE TYPES
// ============================================================================
export const MESSAGE_TYPE = {
  SUCCESS: 'success',
  ERROR: 'error',
  WARNING: 'warning',
  INFO: 'info'
};

// ============================================================================
// LOADING STATES
// ============================================================================
export const LOADING_STATE = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error'
};

// ============================================================================
// FORM VALIDATION
// ============================================================================
export const VALIDATION = {
  REQUIRED: 'required',
  MIN_LENGTH: 'minLength',
  MAX_LENGTH: 'maxLength',
  PATTERN: 'pattern',
  EMAIL: 'email',
  NUMBER: 'number'
};

// ============================================================================
// NETWORK GRAPH CONSTANTS
// ============================================================================
export const GRAPH = {
  NODE: {
    MIN_WIDTH: 220,
    MIN_HEIGHT: 120,
    PADDING: 40
  },
  LAYOUT: {
    COLUMNS: 3,
    HORIZONTAL_GAP: 150,
    VERTICAL_GAP: 150
  },
  EDGE: {
    ARROW_SIZE: 18,
    Z_INDEX: 1000
  }
};

// ============================================================================
// CHAT CONSTANTS
// ============================================================================
export const CHAT = {
  MAX_MESSAGE_LENGTH: 4000,
  TYPING_DELAY: 1000,
  SESSION: {
    DEFAULT_ID: 'default',
    TIMEOUT: 30 * 60 * 1000 // 30 minutes
  }
};

// ============================================================================
// FILE CONSTANTS
// ============================================================================
export const FILE = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: [
    'image/jpeg',
    'image/png',
    'image/gif',
    'text/plain',
    'application/pdf'
  ]
};

export default {
  ANIMATION,
  SIZE,
  SPACING,
  BREAKPOINTS,
  Z_INDEX,
  STATUS,
  VARIANT,
  MESSAGE_TYPE,
  LOADING_STATE,
  VALIDATION,
  GRAPH,
  CHAT,
  FILE
}; 