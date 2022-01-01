const ImportGlobPlugin = require('esbuild-plugin-import-glob').default;
const esbuild = require("esbuild");
const {
  vanillaExtractPlugin
} = require('@vanilla-extract/esbuild-plugin');

require('esbuild').build({
  entryPoints: ['server.tsx'],
  bundle: true,
  platform: "node",
  outfile: 'dist/server.js',
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
  ],
}).catch(() => process.exit(1))
