import { defineConfig } from 'vite'
import { nodePolyfills } from 'vite-plugin-node-polyfills'


export default defineConfig({
  base: '/static/', // Ensure all assets are prefixed with /static/
  plugins: [
    nodePolyfills({
      include: ['buffer', 'crypto', 'stream'], // Only essentials for algosdk and use-wallet
      exclude: ['vm', 'fs', 'path'], // Exclude unused shims
      globals: {
        Buffer: true,
        global: true,
        process: true
      }
    })
  ],
  build: {
    outDir: '../static', // Output to static/ (parent of js/ and css/)
    emptyOutDir: true, // Clear outDir before build
    manifest: 'manifest.json', // Output manifest.json directly to outDir (static/)
    minify: 'esbuild', // Default, but explicit
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        entryFileNames: 'js/bundle.js', // JS to static/js/bundle.js
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: ({ name }) => {
          return 'assets/[name].[ext]'; // Other assets to static/assets/
        },
        manualChunks: undefined // Single bundle for simplicity
      }
    }
  }
})
