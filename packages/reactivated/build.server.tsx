import linaria from "@linaria/esbuild";
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from "esbuild-plugin-import-glob";

esbuild
    .build({
        // entryPoints: ["server/index.tsx"],
        stdin: {
            contents: `
                import {simpleRender} from "reactivated/server";
                simpleRender();
            `,
            resolveDir: process.cwd(),
            loader: "ts",
        },
        bundle: true,
        platform: "node",
        outfile: "./static/dist/server.js",
        sourcemap: true,
        watch: process.env.REACTIVATED_WATCH !== "false",
        plugins: [
            ImportGlobPlugin(),
            vanillaExtractPlugin(),
            linaria({sourceMap: true}),
        ],
    })
    .catch(() => process.exit(1));
