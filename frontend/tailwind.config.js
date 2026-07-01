/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d1117',
        surface: '#161b22',
        border: '#30363d',
        primary: '#e6edf3',
        muted: '#8b949e',
        bull: '#00ff88',
        bear: '#ff4444',
        accent: '#38bdf8',
        orange: '#ffa500',
        purple: '#a78bfa',
      },
    },
  },
  plugins: [],
};
