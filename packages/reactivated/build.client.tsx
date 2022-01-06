import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";

const entryNames = process.argv.slice(2);

const entryPoints = Object.fromEntries(entryNames.map(entry => [entry, `./client/${entry}.tsx`]));

const production = process.env.NODE_ENV === 'production';

esbuild
    .build({
        entryPoints,
        bundle: true,
        minify: production,
        platform: "browser",
        outdir: "./static/dist",
        sourcemap: true,
        watch: production === false,
        define: {
            process: '{"env": {}}',
            global: '{}',
        },
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true}),
        ],
    })
    .catch(() => process.exit(1));
