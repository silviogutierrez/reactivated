//const ImportGlobPlugin = require('esbuild-plugin-import-glob');
const esbuild = require("esbuild");

require('esbuild').build({
  entryPoints: ['index.tsx'],
  bundle: true,
  platform: "node",
  outfile: 'server.js',
}).catch(() => process.exit(1))
