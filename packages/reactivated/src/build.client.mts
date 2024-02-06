#!/usr/bin/env node

import react from '@vitejs/plugin-react'
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";
import {InlineConfig, build} from "vite";
import { builtinModules } from "node:module";
import  path from "path";
import {Options} from "./conf";

const getConfiguration = () => {
  try {
    return import(path.resolve(process.cwd(), "./node_modules/_reactivated/conf.mjs"));
  }
  catch {
    return null;
  }
}


// @ts-ignore
const customConfigurationImport: {default?: Options} | null = await getConfiguration();

const getClientOptions =
    customConfigurationImport?.default?.build?.client != null
        ? customConfigurationImport.default.build.client
        : (options: ClientConfig) => options;

const getRendererOptions =
    customConfigurationImport?.default?.build?.renderer != null
        ? customConfigurationImport.default.build.renderer
        : (options: RendererConfig) => options;

const identifiers = "short";

const clientConfig = {build: {
    emptyOutDir: true,
    // outDir: "static",
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
} satisfies InlineConfig;

const otherExternals: string[] = [];
const external =  [...otherExternals, ...builtinModules, ...builtinModules.map((m) => `node:${m}`)];


const rendererConfig = {
    ssr: {
        external,
        noExternal: true,
    },
  build: {
    emptyOutDir: false,
    // outDir: "static",
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
} satisfies InlineConfig;

export type ClientConfig = typeof clientConfig;

export type RendererConfig = typeof rendererConfig;

await build(getClientOptions(clientConfig));

await build(getRendererOptions(rendererConfig));
