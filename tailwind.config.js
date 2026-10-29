/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/templates/**/*.html",
    "./app/static/js/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        'cig-red': {
          DEFAULT: '#C62828',
          light: '#D32F2F',
          dark: '#B71C1C',
        },
        'cig-green': {
          DEFAULT: '#1B5E20',
          light: '#2E7D32',
          dark: '#0D330E',
        },
        'cig-cream': '#FFF5F5',
        'cig-pink': '#FEE2E2',
      },
      fontFamily: {
        sans: ['Poppins', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
