import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import http from "http";

let server: http.Server | null = null;

const CACHE_KEY = `${process.cwd()}/node_modules/.bin/server.js`;

esbuild
    .build({
        // entryPoints: ["server/index.tsx"],
        stdin: {
            contents: `
                export {server} from "reactivated/server";
            `,
            resolveDir: process.cwd(),
            loader: "ts",
        },
        bundle: true,
        platform: "node",
        outfile: "./node_modules/.bin/server.js",
        sourcemap: true,
        //watch: process.env.REACTIVATED_WATCH !== "false",
        watch: {
            onRebuild: () => {
                if (server != null) {
                    server.close();
                    delete require.cache[CACHE_KEY];
                }
                server = require(CACHE_KEY).server;
            },
        },
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true}),
        ],
    }).then(() =>{
        server = require(CACHE_KEY).server;
    })
    .catch(() => process.exit(1));
