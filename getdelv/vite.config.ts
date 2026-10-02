import { defineConfig } from 'vite';
import htmlMinifier from 'vite-plugin-html-minifier';

// https://vitejs.dev/config/
export default defineConfig({
  // Base public path when served in development or production
  base: '/',
  
  // Development server configuration
  server: {
    port: 3000,
    open: true,
    host: true // Listen on all addresses
  },

  // Build configuration
  build: {
    // Output directory
    outDir: 'dist',
    
    // Clean the output directory before build
    emptyOutDir: true,
    
    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    
    // CSS minification
    cssMinify: true,
    
    // Generate sourcemaps for production builds
    sourcemap: true,
    
    // Asset handling
    assetsDir: 'assets',
    rollupOptions: {
      output: {
        // Hash-based naming for better caching
        entryFileNames: 'assets/[name].[hash].js',
        chunkFileNames: 'assets/[name].[hash].js',
        assetFileNames: 'assets/[name].[hash].[ext]'
      }
    }
  },

  // Plugins
  plugins: [
    htmlMinifier({
      minify: {
        collapseWhitespace: true,
        removeComments: true,
        removeRedundantAttributes: true,
        removeScriptTypeAttributes: true,
        removeStyleLinkTypeAttributes: true,
        useShortDoctype: true,
        minifyCSS: true,
        minifyJS: true
      }
    })
  ],

  // Resolve configuration
  resolve: {
    // Add any path aliases here if needed
  }
});