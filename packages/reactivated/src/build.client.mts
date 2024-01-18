#!/usr/bin/env node

import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import {execSync, exec} from "child_process";
import fs from "fs";

const entryNames = process.argv.slice(2);

const entryPoints = Object.fromEntries(
    entryNames.map((entry) => [entry, `./client/${entry}.tsx`]),
);

const production = process.env.NODE_ENV === "production";
const identifiers = production ? "short" : "debug";

const env = {
    NODE_ENV: production ? "production" : "development",
    BUILD_VERSION: process.env.BUILD_VERSION,
    TAG_VERSION: process.env.TAG_VERSION,
    RELEASE_VERSION: process.env.RELEASE_VERSION,
};

const hasTailwind = fs.existsSync("./tailwind.config.ts");

if (hasTailwind) {
    execSync(
        "npx tailwind -i client/input.css -o ./node_modules/_reactivated/tailwind.css",
        {stdio: "ignore"},
    );
}

esbuild
    .context({
        entryPoints,
        bundle: true,
        // We use terser to minify because esbuild breaks safari sourcemaps.
        // It's likely a Safari bug, but terser seems to work for some reason.
        minify: false,
        // Related to sourcemaps as well in Safari.
        legalComments: "none",
        platform: "browser",
        outdir: "./static/dist",
        sourcemap: true,
        target: "es2018",
        preserveSymlinks: true,
        external: ["@reactivated/images"],
        define: {
            // You need both. The one from the stringified JSON is not picked
            // up during the build process.
            "process.env.NODE_ENV": production ? '"production"' : '"development"',
            process: JSON.stringify({env}),

            // Redux persist needs this.
            global: "{}",
        },
        loader: {
            ".gif": "file",
            ".jpeg": "file",
            ".jpg": "file",
            ".png": "file",
            ".svg": "file",
            ".ttf": "file",
            ".woff": "file",
            ".woff2": "file",
        },
        plugins: [
            // ESM imports make this weird.
            (ImportGlobPlugin as unknown as {default: () => esbuild.Plugin}).default(),
            // We manually pass in identifiers because the client is not
            // minified by esbuild but the renderer is, so class names could
            // differ.
            // Instead of set it manually instead of relying on minification
            // settings.
            vanillaExtractPlugin({identifiers}),
        ],
    })
    .then(async (context) => {
        if (production === false) {
            if (hasTailwind) {
                exec(
                    "npx tailwind -i client/input.css -o ./node_modules/_reactivated/tailwind.css --watch",
                );
            }
            context.watch();
        } else {
            await context.rebuild();
            process.exit();
        }
    });
