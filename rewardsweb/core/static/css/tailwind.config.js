/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/*.html",
    "./templates/**/*.html",
  ],
  plugins: [
    // daisyUI is already loaded via @plugin, but this ensures proper integration
  ],
}