import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from 'esbuild-plugin-import-glob';

esbuild.build({
  entryPoints: ['client.tsx'],
  bundle: true,
  platform: "browser",
  outfile: 'dist/client.js',
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
  ],
}).catch(() => process.exit(1))
