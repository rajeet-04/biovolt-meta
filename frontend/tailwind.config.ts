/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bio: {
          bg: 'rgb(var(--bg) / <alpha-value>)',
          panel: 'rgb(var(--panel) / <alpha-value>)',
          'panel-strong': 'rgb(var(--panel-strong) / <alpha-value>)',
          'panel-raised': 'rgb(var(--panel-raised) / <alpha-value>)',
          text: 'rgb(var(--text) / <alpha-value>)',
          muted: 'rgb(var(--muted) / <alpha-value>)',
          accent: 'rgb(var(--accent) / <alpha-value>)',
          'accent-soft': 'rgb(var(--accent-soft) / <alpha-value>)',
          success: 'rgb(var(--success) / <alpha-value>)',
          warning: 'rgb(var(--warning) / <alpha-value>)',
          danger: 'rgb(var(--danger) / <alpha-value>)',
          border: 'rgb(var(--border) / <alpha-value>)',
          focus: 'rgb(var(--focus) / <alpha-value>)',
        },
      },
    },
  },
}
