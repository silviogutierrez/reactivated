const ImportGlobPlugin = require('esbuild-plugin-import-glob').default;
const esbuild = require("esbuild");

require('esbuild').build({
  entryPoints: ['client.tsx'],
  bundle: true,
  platform: "browser",
  outfile: 'dist/client.js',
  plugins: [
      ImportGlobPlugin(),
  ],
}).catch(() => process.exit(1))
