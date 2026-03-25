/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'siem-bg': '#0f172a',
        'siem-surface': '#1e293b',
        'siem-border': '#334155',
        'siem-text': '#e2e8f0',
        'siem-muted': '#94a3b8',
        'siem-accent': '#3b82f6',
        severity: {
          critical: '#ef4444',
          high: '#f97316',
          medium: '#eab308',
          low: '#3b82f6',
          info: '#6b7280',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
