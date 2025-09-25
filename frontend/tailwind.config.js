/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: 'var(--primary)',
        'primary-dark': 'var(--primary-dark)',
        accent: 'var(--accent)',
        neutral: 'var(--neutral)',
        text: 'var(--text)',
        white: 'var(--white)',
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'], // Exemple, à ajuster si besoin
      }
    },
  },
  plugins: [],
}