import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    server: {
        proxy: {},
    },
    resolve: {
        alias: {
            '@client': path.resolve(__dirname, './client'),
            '@reactivated': path.resolve(__dirname, './node_modules/_reactivated'),
        },
    },
    build: {
        manifest: true,
        rollupOptions: {
            input: "client/index.tsx",
        },
    },
});
