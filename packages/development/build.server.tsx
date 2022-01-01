import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from 'esbuild-plugin-import-glob';

esbuild.build({
  entryPoints: ['server.tsx'],
  bundle: true,
  platform: "node",
  outfile: 'dist/server.js',
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
  ],
}).catch(() => process.exit(1))
