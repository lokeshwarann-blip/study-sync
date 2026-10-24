/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        pink: {
          DEFAULT: '#ffa6e6',
          dim: 'rgba(255, 166, 230, 0.55)',
          glow: 'rgba(255, 166, 230, 0.25)',
        }
      },
      fontFamily: {
        syne: ['Syne', 'sans-serif'],
        space: ['Space Grotesk', 'sans-serif'],
        serif: ['Instrument Serif', 'serif'],
      }
    },
  },
  plugins: [],
}
