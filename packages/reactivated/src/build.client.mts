#!/usr/bin/env node

import react from "@vitejs/plugin-react";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {InlineConfig, build} from "vite";
import {builtinModules} from "node:module";
import path from "path";
import {define, Options} from "./conf.js";

const identifiers = "short";

const clientConfig = {
    define: define(),
    build: {
        minify: false,
        target: "esnext",
        sourcemap: true,
        emptyOutDir: true,
        outDir: "static/dist",
        manifest: false,
        rollupOptions: {
            input: "/client/index.tsx",
            output: {
                inlineDynamicImports: true,
                entryFileNames: `[name].js`,
                chunkFileNames: `[name].js`,
                assetFileNames: `[name].[ext]`,
            },
        },
    },

    plugins: [react(), vanillaExtractPlugin({identifiers})],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
} satisfies InlineConfig;

const otherExternals: string[] = [];
const external = [
    ...otherExternals,
    ...builtinModules,
    ...builtinModules.map((m) => `node:${m}`),
];

const rendererConfig = {
    ssr: {
        external,
        noExternal: true,
    },
    build: {
        sourcemap: true,
        emptyOutDir: false,
        outDir: "./node_modules/_reactivated/",
        ssr: true,
        manifest: false,
        rollupOptions: {
            input: "reactivated/dist/server.mjs",
            output: {
                inlineDynamicImports: true,
                entryFileNames: `renderer.mjs`,
                chunkFileNames: `renderer.mjs`,
                assetFileNames: `renderer.[ext]`,
            },
            external,
        },
    },

    plugins: [react(), vanillaExtractPlugin({identifiers})],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
} satisfies InlineConfig;

export type ClientConfig = typeof clientConfig;

export type RendererConfig = typeof rendererConfig;

await build(clientConfig);
await build(rendererConfig);
