import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";

const entryNames = process.argv.slice(2);

const entryPoints = Object.fromEntries(entryNames.map(entry => [entry, `./client/${entry}.js`]));

esbuild
    .build({
        entryPoints,
        bundle: true,
        platform: "browser",
        outdir: "./static/dist",
        sourcemap: true,
        watch: true,
        define: {
            // process: '{"env": {}}',
            global: '{}',
        },
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true}),
        ],
    })
    .catch(() => process.exit(1));
