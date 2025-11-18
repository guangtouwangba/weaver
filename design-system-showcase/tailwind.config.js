/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          page: '#F5F6F9',
          card: '#FFFFFF',
          subtle: '#F9FAFB',
        },
        text: {
          primary: '#111827',
          secondary: '#4B5563',
          muted: '#9CA3AF',
          'on-accent': '#FFFFFF',
          'on-warning': '#1F2933',
          'on-positive': '#064E3B',
        },
        border: {
          subtle: '#E5E7EB',
          strong: '#D1D5DB',
          focus: '#2563EB',
        },
        primary: {
          strong: '#3B82F6',
          soft: '#E0ECFF',
          hover: '#2563EB',
          pressed: '#1D4ED8',
        },
        secondary: {
          indigo: '#6366F1',
          purple: '#8B5CF6',
          pink: '#EC4899',
        },
        emerald: {
          strong: '#10B981',
          soft: '#D1FAE5',
        },
        orange: {
          strong: '#F97316',
          soft: '#FFEDD5',
        },
        yellow: {
          strong: '#FACC15',
          soft: '#FEF9C3',
        },
        red: {
          strong: '#F97373',
          soft: '#FEE2E2',
        },
        status: {
          info: '#3B82F6',
          success: '#10B981',
          warning: '#FBBF24',
          error: '#F97373',
          neutral: '#6B7280',
        },
      },
      spacing: {
        'xxs': '4px',
        'xs': '8px',
        'sm': '12px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        'xxl': '40px',
      },
      borderRadius: {
        'xs': '4px',
        'sm': '8px',
        'md': '12px',
        'lg': '16px',
        'pill': '999px',
      },
      boxShadow: {
        'none': 'none',
        'soft': '0 4px 16px 0 rgba(15, 23, 42, 0.08)',
        'medium': '0 8px 24px 0 rgba(15, 23, 42, 0.12)',
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'SF Pro Text', 'Inter', 'sans-serif'],
      },
      fontSize: {
        'display-lg': ['32px', { lineHeight: '1.25', fontWeight: '600' }],
        'display-md': ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        'title': ['20px', { lineHeight: '1.3', fontWeight: '600' }],
        'subtitle': ['16px', { lineHeight: '1.4', fontWeight: '500' }],
        'body': ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        'body-bold': ['14px', { lineHeight: '1.5', fontWeight: '600' }],
        'caption': ['12px', { lineHeight: '1.5', fontWeight: '400' }],
        'label': ['11px', { lineHeight: '1.4', fontWeight: '600' }],
      },
      transitionDuration: {
        'fast': '120ms',
        'normal': '180ms',
        'slow': '240ms',
      },
      transitionTimingFunction: {
        'standard': 'cubic-bezier(0.2, 0.8, 0.2, 1)',
        'emphasized': 'cubic-bezier(0.2, 1, 0.2, 1)',
      },
      maxWidth: {
        'content': '1280px',
      },
    },
  },
  plugins: [],
}

