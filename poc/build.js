const ImportGlobPlugin = require('esbuild-plugin-import-glob').default;
const esbuild = require("esbuild");

require('esbuild').build({
  entryPoints: ['index.tsx'],
  bundle: true,
  platform: "node",
  outfile: 'dist/server.js',
  plugins: [
      ImportGlobPlugin(),
  ],
}).catch(() => process.exit(1))
