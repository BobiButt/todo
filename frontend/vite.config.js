// ============================================================================
// FILE:       frontend/vite.config.ts
// PURPOSE:    Vite build and development server configuration.
//             Configures React plugin, path aliases, API proxy, and
//             production build optimizations for Vercel deployment.
// HOW IT WORKS: Maps /api requests to http://localhost:8000 during local
//             development. Bundles with ESBuild and Rollup for production.
// USED BY / DEPENDS ON: npm run dev, npm run build, frontend source files.
// ============================================================================
import path from "path";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        port: 5173,
        proxy: {
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
            },
        },
    },
    // Inject API_BASE_URL (set in Vercel Env Vars or .env) at build time so
    // client.ts can read import.meta.env.API_BASE_URL (Vite only inlines VITE_*
    // variables by default).
    define: {
        "import.meta.env.API_BASE_URL": JSON.stringify(process.env.API_BASE_URL || process.env.VITE_API_BASE_URL || "/api/v1"),
    },
    build: {
        outDir: "dist",
        sourcemap: false,
        minify: "esbuild",
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ["react", "react-dom", "react-router-dom", "sonner"],
                    ui: ["lucide-react", "@tanstack/react-query", "@dnd-kit/core"],
                },
            },
        },
    },
});
