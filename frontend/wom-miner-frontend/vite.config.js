import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import {BASE} from "./src/config/config";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy:{
      '/elastic': {
        target: 'https://wom.handte.org',
        changeOrigin: true,
        configure: (proxy, options) => {
          const fs = require("fs")
          const toml = require("toml")
          const config = toml.parse(fs.readFileSync('../../config/elastic.frontend.toml', 'utf-8'));
          options.auth = `${config.username}:${config.password}`;
        }
      }
    }
  },
  base: BASE
})