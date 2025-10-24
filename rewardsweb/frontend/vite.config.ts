import { defineConfig } from 'vite'
import { nodePolyfills } from 'vite-plugin-node-polyfills'

export default defineConfig({
  plugins: [nodePolyfills()],
  build: {
    outDir: '../static', // Output to static/ (parent of js/ and css/)
    emptyOutDir: true, // Clear outDir before build
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        entryFileNames: 'js/bundle.js', // JS to static/js/bundle.js
        assetFileNames: ({ name }) => {
          if (name && name.endsWith('.css')) {
            return 'css/bundle.css'; // CSS to static/css/bundle.css
          }
          return 'assets/[name].[ext]'; // Other assets to static/assets/
        }
      }
    }
  }
})