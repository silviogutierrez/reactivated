#!/usr/bin/env node

import react from '@vitejs/plugin-react'
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {build} from "vite";
import  path from "path";

// await build({
//   build: {
//     // generate .vite/manifest.json in outDir
//     manifest: true,
//     rollupOptions: {
//       // overwrite default .html entry
//       input: '/client/index.tsx',
//       output: {
//         entryFileNames: `assets/[name].js`,
//         chunkFileNames: `assets/[name].js`,
//         assetFileNames: `assets/[name].[ext]`
//       }
//     },
//   },
// 
//     plugins: [react(), vanillaExtractPlugin()],
//     resolve: {
//         alias: {
//             "@client": path.resolve(process.cwd(), "./client"),
//             "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
//         },
//     },
// })
//
import { builtinModules } from "node:module";
const otherExternals: string[] = [];
const external =  [...otherExternals, ...builtinModules, ...builtinModules.map((m) => `node:${m}`)];

await build({
    ssr: {
        external,
        noExternal: true,
    },
  build: {
    // generate .vite/manifest.json in outDir
    // minify: false,
    // target: "esnext",
    ssr: true,
    manifest: true,
    rollupOptions: {
      // overwrite default .html entry
      input: 'reactivated/dist/server.mjs',
      output: {
        entryFileNames: `assets/server.[name].mjs`,
        chunkFileNames: `assets/server.[name].mjs`,
        assetFileNames: `assets/server.[name].[ext]`
      },
      external,
    },
  },

  plugins: [react(), vanillaExtractPlugin()],
  resolve: {
      alias: {
          "@client": path.resolve(process.cwd(), "./client"),
          "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
      },
  },
})
