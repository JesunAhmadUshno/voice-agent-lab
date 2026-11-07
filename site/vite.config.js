import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// The site reads the committed level-*/results_*.json and README files at build time, so every number on the
// page is generated from the repo, never typed. src/voice.check.mjs runs first and fails the build on any drift.
export default defineConfig({
  base: '/voice-agent-lab/',
  plugins: [react()],
  server: { fs: { allow: ['..'] } },
});
