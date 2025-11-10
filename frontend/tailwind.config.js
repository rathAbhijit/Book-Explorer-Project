/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gray: {
          850: "#1E1E2F", // custom shade you already use
        },
      },
    },
  },
  plugins: [require('@tailwindcss/line-clamp')],
};
