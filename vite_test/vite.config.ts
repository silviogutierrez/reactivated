import {defineConfig} from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import linaria from "@linaria/vite";

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [vanillaExtractPlugin(), linaria({
      include: ['**/*.{ts,tsx}'],
      babelOptions: {
        presets: ['@babel/preset-typescript', '@babel/preset-react'],
      },
    }), react()],
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
