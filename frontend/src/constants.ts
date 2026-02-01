// ============================================================================
// UNIFIED COLOR PALETTE - Modern, Professional, Whimsical
// ============================================================================

// PRIMARY BRAND COLORS
export const colors = {
  // Brand colors
  teal: '#49dfb5',           // Primary actions, header, buttons
  purple: '#667eea',         // Secondary accent, hover states
  deepPurple: '#764ba2',     // Tertiary, special emphasis

  // Neutral palette
  darkText: '#1a202c',       // Primary text
  medText: '#2d3748',        // Secondary text, headers
  lightText: '#718096',      // Tertiary text, hints
  lightBg: '#f7fafc',        // Input backgrounds, pages
  white: '#ffffff',          // Cards, content areas
  darkFooter: '#2d3748',     // Footer background
  borderColor: '#e2e8f0',    // Form borders

  // Semantic colors
  error: '#f56565',          // Errors, delete actions
  success: '#48bb78',        // Success states
  warning: '#ecc94b',        // Warnings
  info: '#4299e1',           // Information

  // Legacy support
  rightMoveBlue: '#49dfb5',  // For existing code
};

// TYPOGRAPHY SCALES
export const typography = {
  pageTitle: {
    fontSize: '2.5rem',
    fontWeight: 700,
    color: colors.darkText,
  },
  sectionTitle: {
    fontSize: '1.5rem',
    fontWeight: 700,
    color: colors.medText,
  },
  cardTitle: {
    fontSize: '1.25rem',
    fontWeight: 700,
    color: colors.darkText,
  },
  body: {
    fontSize: '1rem',
    fontWeight: 400,
    color: colors.darkText,
  },
  label: {
    fontSize: '0.95rem',
    fontWeight: 500,
    color: colors.medText,
  },
  small: {
    fontSize: '0.85rem',
    fontWeight: 400,
    color: colors.lightText,
  },
};

// SPACING SYSTEM (8px base unit)
export const spacing = {
  xs: '0.5rem',   // 4px
  sm: '0.75rem',  // 6px
  md: '1rem',     // 8px
  lg: '1.5rem',   // 12px
  xl: '2rem',     // 16px
  xxl: '3rem',    // 24px
};

// BORDER RADIUS
export const borderRadius = {
  cards: '16px',
  buttons: '8px',
  inputs: '8px',
  tags: '6px',
  small: '4px',
};

// SHADOWS
export const shadows = {
  subtle: '0 2px 4px rgba(0,0,0,0.05)',
  light: '0 4px 12px rgba(0,0,0,0.08)',
  medium: '0 10px 30px rgba(0,0,0,0.12)',
  card: '0 10px 40px rgba(0,0,0,0.15)',
  hover: '0 12px 40px rgba(73,223,181,0.2)',
};

// ANIMATIONS
export const animations = {
  fast: '150ms ease-in-out',
  base: '300ms ease-in-out',
  slow: '500ms ease-in-out',
};
