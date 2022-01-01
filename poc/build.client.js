const ImportGlobPlugin = require('esbuild-plugin-import-glob').default;
const esbuild = require("esbuild");
const {
  vanillaExtractPlugin
} = require('@vanilla-extract/esbuild-plugin');

require('esbuild').build({
  entryPoints: ['client.tsx'],
  bundle: true,
  platform: "browser",
  outfile: 'dist/client.js',
  plugins: [
      ImportGlobPlugin(),
      vanillaExtractPlugin(),
  ],
}).catch(() => process.exit(1))
