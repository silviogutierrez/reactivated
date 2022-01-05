import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";
import http from "http";
import fs = require('fs')

let server: http.Server | null = null;

const SOCKET_PATH = "./node_modules/.bin/reactivated.sock";
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
                restartServer();
            },
        },
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true}),
        ],
    }).then(() =>{
        restartServer()
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
}
