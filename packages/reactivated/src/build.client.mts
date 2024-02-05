#!/usr/bin/env node

import react from '@vitejs/plugin-react'
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {build} from "vite";
import  path from "path";

const identifiers = "short";

await build({
  build: {
    emptyOutDir: true,
    outDir: "static",
    // generate .vite/manifest.json in outDir
    manifest: false,
    rollupOptions: {
      // overwrite default .html entry
      input: '/client/index.tsx',
      output: {
        entryFileNames: `dist/[name].js`,
        chunkFileNames: `dist/[name].js`,
        assetFileNames: `dist/[name].[ext]`
      }
    },
  },

    plugins: [react(), vanillaExtractPlugin({identifiers})],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
})

import { builtinModules } from "node:module";
const otherExternals: string[] = [];
const external =  [...otherExternals, ...builtinModules, ...builtinModules.map((m) => `node:${m}`)];

await build({
    ssr: {
        external,
        noExternal: true,
    },
  build: {
    emptyOutDir: false,
    outDir: "static",
    // generate .vite/manifest.json in outDir
    // minify: false,
    // target: "esnext",
    ssr: true,
    manifest: false,
    rollupOptions: {
      // overwrite default .html entry
      input: 'reactivated/dist/server.mjs',
      output: {
        entryFileNames: `dist/server.[name].mjs`,
        chunkFileNames: `dist/server.[name].mjs`,
        assetFileNames: `dist/server.[name].[ext]`
      },
      external,
    },
  },

  plugins: [react(), vanillaExtractPlugin({identifiers})],
  resolve: {
      alias: {
          "@client": path.resolve(process.cwd(), "./client"),
          "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
      },
  },
})
