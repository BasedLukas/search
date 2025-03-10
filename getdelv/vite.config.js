import { defineConfig } from 'vite';
import htmlMinifier from 'vite-plugin-html-minifier';

export default defineConfig({
  root: 'src',
  plugins: [
    htmlMinifier({
      minify: true
    })
  ],
  server: {
    open: true
  },
  build: {
    outDir: '../dist',
    emptyOutDir: true
  }
}); 