import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import http from "http";
import fs = require("fs");

let server: http.Server | null = null;

const SOCKET_PATH = `${process.cwd()}/node_modules/.bin/reactivated.sock`;
const CACHE_KEY = `${process.cwd()}/node_modules/.bin/renderer.js`;
const production = process.env.NODE_ENV === "production";

esbuild
    .build({
        stdin: {
            contents: `
                export {server} from "reactivated/renderer";
            `,
            resolveDir: process.cwd(),
            loader: "ts",
        },
        minify: production,
        bundle: true,
        platform: "node",
        outfile: "./node_modules/.bin/renderer.js",
        sourcemap: true,
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
            vanillaExtractPlugin(),
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

    if (fs.existsSync(SOCKET_PATH)) {
        fs.unlinkSync(SOCKET_PATH);
    }
    delete require.cache[CACHE_KEY];
    server = require(CACHE_KEY).server;
};
