import linaria from '@linaria/esbuild';
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from 'esbuild-plugin-import-glob';

esbuild.build({
  entryPoints: ['server/index.tsx'],
  bundle: true,
  platform: "node",
  outfile: './static/dist/server.js',
  sourcemap: true,
  watch: true,
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
      linaria({sourceMap: true}),
  ],
}).catch(() => process.exit(1))
