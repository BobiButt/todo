// ============================================================================
// FILE:       frontend/vite.config.ts
// PURPOSE:    Vite build and development server configuration.
//             Configures React plugin, path aliases (@ -> src), and API proxy.
// HOW IT WORKS: Maps /api requests to http://localhost:8000 during local development
//             to eliminate CORS issues. Bundles with ESBuild and Rollup.
// USED BY / DEPENDS ON: npm run dev, npm run build, frontend source files.
// KEY CONCEPTS: Bundler configuration, reverse proxy, path aliasing, Fast Refresh.
// ============================================================================
// path provides Node.js directory resolution tools.
import path from "path";
// defineConfig provides type safety and autocompletion for Vite configuration.
import { defineConfig } from "vite";
// plugin-react provides JSX compilation and React Fast Refresh.
import react from "@vitejs/plugin-react";
// Export Vite configuration object.
export default defineConfig({
    // Attach React plugin for JSX transformation.
    plugins: [react()],
    // Resolve directory aliases.
    resolve: {
        alias: {
            // Map '@/' imports directly to the './src/' folder.
            "@": path.resolve(__dirname, "./src"),
        },
    },
    // Development server configuration.
    server: {
        // Port 5173 matching standard Vite dev convention and backend CORS whitelist.
        port: 5173,
        // Proxy API requests to backend during local development.
        proxy: {
            "/api": {
                // Target FastAPI backend port.
                target: "http://localhost:8000",
                // Change origin header to match backend host.
                changeOrigin: true,
            },
        },
    },
});
