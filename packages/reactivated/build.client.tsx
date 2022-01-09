import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";

const entryNames = process.argv.slice(2);

const entryPoints = Object.fromEntries(
    entryNames.map((entry) => [entry, `./client/${entry}.tsx`]),
);

const production = process.env.NODE_ENV === "production";

const env = {
    NODE_ENV: production ? "production" : "development",
    BUILD_VERSION: process.env.BUILD_VERSION,
    TAG_VERSION: process.env.TAG_VERSION,
};

esbuild
    .build({
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
        watch: production === false,
        external: ["moment", "@client/generated/images"],
        define: {
            // You need both. The one from the stringified JSON is not picked
            // up during the build process.
            "process.env.NODE_ENV": production ? '"production"' : '"development"',
            process: JSON.stringify({env}),

            // Redux persist needs this.
            global: "{}",
        },
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true, esbuildOptions: {sourcemap: "inline"}}),
        ],
    })
    .catch(() => process.exit(1));
