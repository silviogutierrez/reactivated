#!/usr/bin/env node

import react from "@vitejs/plugin-react";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {InlineConfig, build} from "vite";
import {builtinModules} from "node:module";
import {execSync} from "child_process";
import path from "path";
import {existsSync, mkdirSync, rmSync} from "fs";
import {define, Options} from "./conf.js";
import * as esbuild from "esbuild";
import {promises as fs} from "fs";

const REACTIVATED_WATCH = "REACTIVATED_WATCH" in process.env;

const {minify, mode, watch} =
    REACTIVATED_WATCH == true
        ? {minify: false, watch: {}, mode: "development"}
        : {minify: true, watch: undefined, mode: "production"};

export default function capacitorPlugin() {
    return {
        name: "capacitor-plugin",

        writeBundle() {
            const sourcePath = "static";
            const targetPath = "capacitor/ios/App/App/public/static";

            rmSync(targetPath, {force: true, recursive: true});
            execSync(`cp -R ${sourcePath} ${targetPath}`);
            console.log("Capacitor files copied");
        },
    };
}

const base = process.env.BASE ?? "/";
const identifiers = "short";

const clientConfig = {
    define: define(),
    mode,
    build: {
        minify,
        watch,
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
    plugins: [capacitorPlugin(), react(), vanillaExtractPlugin({identifiers})],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
    base,
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
    base,
} satisfies InlineConfig;

export type ClientConfig = typeof clientConfig;

export type RendererConfig = typeof rendererConfig;

await build(clientConfig);

if (watch == null) {
    await build(rendererConfig);
    // Currently, vanilla-extract plugins are not bundled even though we tell rollup
    // to bundle in the renderer build. So we do an esbuild pass after. Really clunky.
    await esbuild.build({
        sourcemap: true,
        entryPoints: ["./node_modules/_reactivated/renderer.mjs"],
        bundle: true,
        platform: "node",
        outfile: "./node_modules/_reactivated/renderer.js",
    });
    await fs.unlink("./node_modules/_reactivated/renderer.mjs");
    await fs.unlink("./node_modules/_reactivated/renderer.mjs.map");
}
