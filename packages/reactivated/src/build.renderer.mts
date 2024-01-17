#!/usr/bin/env node

import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import http from "http";
import fs from "fs";
import path from "path";
import {createRequire} from "module";

let server: http.Server | null = null;

const CACHE_KEY = `${process.cwd()}/node_modules/_reactivated/renderer.js`;
const production = process.env.NODE_ENV === "production";
const identifiers = production ? "short" : "debug";

const restartServer = async () => {
    if (server != null) {
        server.close();
    }

    const modulePath = path.resolve(CACHE_KEY);

    // https://ar.al/2021/02/22/cache-busting-in-node.js-dynamic-esm-imports/
    const require = createRequire(import.meta.url);
    delete require.cache[CACHE_KEY];
    server = require(CACHE_KEY).server;
};

await esbuild.build({
  entryPoints: ['./reactivated.config.tsx'],
  bundle: false,
  outfile: './node_modules/_reactivated/conf.js',
});

esbuild
    .context({
        stdin: {
            contents: `
                export {server, currentTime} from "reactivated/dist/renderer";
            `,
            resolveDir: process.cwd(),
            loader: "ts",
        },
        minify: production,
        bundle: true,
        platform: "node",
        outfile: "./node_modules/_reactivated/renderer.js",
        sourcemap: true,
        target: "es2018",
        preserveSymlinks: true,
        // Needed so _reactivated is included in renderer.tsx regardless
        // of the location of reactivated being in the cwd node_modules or
        // above as in monorepos.
        nodePaths: [`${process.cwd()}/node_modules`],
        plugins: [
            // ESM imports make this weird.
            (ImportGlobPlugin as unknown as {default: () => esbuild.Plugin}).default(),
            // We manually pass in identifiers because the client is not
            // minified by esbuild but the renderer is, so class names could
            // differ.
            // Instead of set it manually instead of relying on minification
            // settings.
            vanillaExtractPlugin({identifiers}),
            {
                name: "restartServer",
                setup: (build) => {
                    if (production === false) {
                        build.onEnd((result) => {
                            restartServer();
                        });
                    }
                },
            },
        ],
    })
    .then(async (context) => {
        if (production === false) {
            context.watch();
        } else {
            await context.rebuild();
            process.exit();
        }
    });
