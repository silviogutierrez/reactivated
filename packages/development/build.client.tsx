import linaria from '@linaria/esbuild';
import {vanillaExtractPlugin} from "@vanilla-extract/esbuild-plugin";
import * as esbuild from "esbuild";
import ImportGlobPlugin from 'esbuild-plugin-import-glob';

esbuild.build({
  entryPoints: ['client/index.tsx'],
  bundle: true,
  platform: "browser",
  outfile: 'dist/client.js',
  sourcemap: true,
    define: {
        "process": '{"env": {}}',
    },
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
      linaria({sourceMap: true}),
  ],
}).catch(() => process.exit(1))
