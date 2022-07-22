#!/usr/bin/env node

import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import http from "http";
import fs = require("fs");

let server: http.Server | null = null;

const CACHE_KEY = `${process.cwd()}/node_modules/_reactivated/renderer.js`;
const production = process.env.NODE_ENV === "production";
const identifiers = production ? "short" : "debug";

esbuild
    .build({
        stdin: {
            contents: `
                export {server} from "reactivated/dist/renderer";
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
        watch:
            production === true
                ? false
                : {
                      onRebuild: () => {
                          restartServer();
                      },
                  },
        plugins: [
            ImportGlobPlugin(),
            // We manually pass in identifiers because the client is not
            // minified by esbuild but the renderer is, so class names could
            // differ.
            // Instead of set it manually instead of relying on minification
            // settings.
            vanillaExtractPlugin({identifiers}),
            linaria({sourceMap: true}),
        ],
    })
    .then(() => {
        if (production === false) {
            restartServer();
        }
    })
    .catch(() => process.exit(1));

const restartServer = () => {
    if (server != null) {
        server.close();
    }

    delete require.cache[CACHE_KEY];
    server = require(CACHE_KEY).server;
};
