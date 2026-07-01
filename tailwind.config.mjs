/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Playfair Display', 'Georgia', 'serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        brand: {
          50: '#fdf4ff',
          100: '#fae8ff',
          200: '#f5d0fe',
          300: '#f0abfc',
          400: '#e879f9',
          500: '#d946ef',
          600: '#c026d3',
          700: '#a21caf',
          800: '#86198f',
          900: '#701a75',
        },
        surface: {
          50: '#fafafa',
          100: '#f4f4f5',
          200: '#e4e4e7',
          300: '#d4d4d8',
          400: '#a1a1aa',
          500: '#71717a',
          600: '#52525b',
          700: '#3f3f46',
          800: '#27272a',
          900: '#18181b',
          950: '#09090b',
        },
      },
      typography: {
        DEFAULT: {
          css: {
            maxWidth: '72ch',
            fontSize: '1.125rem',
            lineHeight: '1.8',
            color: '#3f3f46',
            a: {
              color: '#c026d3',
              textDecoration: 'underline',
              textDecorationColor: '#f0abfc',
              fontWeight: '500',
              '&:hover': {
                color: '#a21caf',
                textDecorationColor: '#c026d3',
              },
            },
            h1: {
              fontWeight: '800',
              letterSpacing: '-0.03em',
              color: '#18181b',
            },
            h2: {
              fontWeight: '700',
              letterSpacing: '-0.025em',
              color: '#27272a',
              marginTop: '2em',
            },
            h3: {
              fontWeight: '600',
              letterSpacing: '-0.02em',
              color: '#3f3f46',
            },
            blockquote: {
              borderLeftColor: '#d946ef',
              borderLeftWidth: '3px',
              fontStyle: 'italic',
              backgroundColor: '#fdf4ff',
              padding: '1rem 1.5rem',
              borderRadius: '0 0.5rem 0.5rem 0',
              color: '#701a75',
            },
            code: {
              backgroundColor: '#f4f4f5',
              padding: '0.25rem 0.5rem',
              borderRadius: '0.375rem',
              fontWeight: '500',
              fontSize: '0.875em',
              border: '1px solid #e4e4e7',
            },
            'code::before': { content: 'none' },
            'code::after': { content: 'none' },
            pre: {
              backgroundColor: '#18181b',
              color: '#e4e4e7',
              borderRadius: '0.75rem',
              padding: '1.25rem',
              border: '1px solid #3f3f46',
            },
            'pre code': {
              backgroundColor: 'transparent',
              padding: '0',
              border: 'none',
              color: 'inherit',
            },
            hr: {
              borderColor: '#e4e4e7',
              marginTop: '2em',
              marginBottom: '2em',
            },
            table: {
              fontSize: '0.9375rem',
            },
            th: {
              fontWeight: '600',
              color: '#27272a',
            },
          },
        },
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-out',
        'slide-up': 'slideUp 0.5s ease-out',
        'slide-in-left': 'slideInLeft 0.5s ease-out',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInLeft: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(217, 70, 239, 0.15)' },
          '100%': { boxShadow: '0 0 40px rgba(217, 70, 239, 0.3)' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'noise': "url(\"data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};
