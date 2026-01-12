import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.{test,spec}.{js,ts,tsx}'],
    exclude: ['node_modules', '.next'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules', '.next', '**/*.d.ts'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
