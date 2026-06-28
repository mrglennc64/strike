/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'trading-bg': '#0a0e27',
        'trading-card': '#141829',
        'trading-border': '#2a2f4a',
        'trading-text': '#e0e6ff',
        'trading-accent': '#00d4ff',
        'trading-success': '#00c853',
        'trading-danger': '#ff3838',
        'trading-warning': '#ffa500',
      },
      fontFamily: {
        'mono': ['Courier New', 'monospace'],
      },
    },
  },
  plugins: [],
}
