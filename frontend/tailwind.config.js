/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EFF6FF', 100: '#DBEAFE', 200: '#BFDBFE', 300: '#93C5FD',
          400: '#60A5FA', 500: '#3B82F6', 600: '#2563EB', 700: '#1D4ED8',
          800: '#1E40AF', 900: '#1E3A8A',
        },
        amber: { 500: '#F59E0B', 600: '#D97706' },
        success: { 500: '#10B981', 600: '#059669' },
        danger: { 500: '#EF4444', 600: '#DC2626' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      borderRadius: { 'xl': '12px', '2xl': '16px' },
      boxShadow: {
        'card': '0 1px 3px rgba(0,0,0,0.1)',
        'card-hover': '0 4px 12px rgba(0,0,0,0.15)',
      },
    },
  },
  plugins: [],
}
