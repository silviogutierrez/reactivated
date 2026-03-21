#!/usr/bin/env node

import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import {InlineConfig, build} from "vite";
import {builtinModules} from "node:module";
import {execSync} from "child_process";
import path from "path";
import {rmSync, existsSync} from "fs";
import {define} from "./conf.js";

const REACTIVATED_WATCH = "REACTIVATED_WATCH" in process.env;

const {minify, mode, watch} =
    REACTIVATED_WATCH == true
        ? {minify: false, watch: {}, mode: "development"}
        : {minify: true, watch: undefined, mode: "production"};

export default function capacitorPlugin() {
    return {
        name: "capacitor-plugin",

        writeBundle() {
            if (watch == null) {
                return;
            }

            const sourcePath = "static";
            const targetPath = "capacitor/ios/App/App/public/static";

            rmSync(targetPath, {force: true, recursive: true});
            execSync(`cp -R ${sourcePath} ${targetPath}`);
            console.log("Capacitor files copied");
        },
    };
}

const base = process.env.BASE ?? "/";

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
        rolldownOptions: {
            input: "/client/index.tsx",
            output: {
                inlineDynamicImports: true,
                entryFileNames: `[name].js`,
                chunkFileNames: `[name].js`,
                assetFileNames: `[name].[ext]`,
            },
        },
    },
    plugins: [capacitorPlugin(), react(), tailwindcss()],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
    base,
} satisfies InlineConfig;

const adminConfig: InlineConfig = {
    ...clientConfig,
    build: {
        ...clientConfig.build,
        emptyOutDir: false,
        rolldownOptions: {
            ...clientConfig.build.rolldownOptions,
            input: "/client/django.admin.tsx",
            output: {
                ...clientConfig.build.rolldownOptions.output,
                entryFileNames: "django.admin.js",
                chunkFileNames: "django.admin.js",
                assetFileNames: "django.admin.[ext]",
            },
        },
    },
};

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
        rolldownOptions: {
            input: "reactivated/dist/server.mjs",
            output: {
                inlineDynamicImports: true,
                entryFileNames: `renderer.mjs`,
                chunkFileNames: `renderer.mjs`,
                assetFileNames: `[name].[ext]`,
            },
            external,
        },
    },

    plugins: [react(), tailwindcss()],
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
    if (existsSync("./client/django.admin.tsx")) {
        await build(adminConfig);
    }

    await build(rendererConfig);
}
