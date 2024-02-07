#!/usr/bin/env node

import react from "@vitejs/plugin-react";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {InlineConfig, build} from "vite";
import {builtinModules} from "node:module";
import path from "path";
import {Options} from "./conf";

const identifiers = "short";

const clientConfig = {
    build: {
        emptyOutDir: true,
        outDir: "static",
        manifest: false,
        rollupOptions: {
            input: "/client/index.tsx",
            output: {
                entryFileNames: `dist/[name].js`,
                chunkFileNames: `dist/[name].js`,
                assetFileNames: `dist/[name].[ext]`,
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
        emptyOutDir: false,
        outDir: "static",
        ssr: true,
        manifest: false,
        rollupOptions: {
            input: "reactivated/dist/server.mjs",
            output: {
                entryFileNames: `dist/renderer.mjs`,
                chunkFileNames: `dist/renderer.mjs`,
                assetFileNames: `dist/renderer.[ext]`,
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
