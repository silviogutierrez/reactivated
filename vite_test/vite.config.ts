import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vanillaExtractPlugin(), react()],
    server: {
        proxy: {},
    },
    resolve: {
        alias: {
            "@client": path.resolve(__dirname, "./client"),
            "@reactivated": path.resolve(__dirname, "./node_modules/_reactivated"),
        },
    },
    build: {
        manifest: true,
        rollupOptions: {
            input: "client/index.tsx",
        },
    },
});
