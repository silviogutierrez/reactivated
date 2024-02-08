import React from "react";
import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";
import ReactDOMServer from "react-dom/server";
import type {render as renderType} from "./render.mjs";
import type {Options} from "./conf";
import type {RendererConfig} from "./build.client.mjs";
import {resolveConfig, mergeConfig, loadConfigFromFile, InlineConfig} from "vite";

import { cjsInterop } from "vite-plugin-cjs-interop";

import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

const isProduction = process.env.NODE_ENV === "production";
const port = process.env.REACTIVATED_VITE_PORT || 5173;
const base = process.env.BASE || "/";
const escapedBase = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const reactivatedEndpoint = "/_reactivated/".replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const app = express();
const {createServer} = await import("vite");

const rendererConfig: InlineConfig = {
    clearScreen: false,
    /*
    optimizeDeps: {
        disabled: true,
    },
    ssr: {
        optimizeDeps: {disabled: true},
    },
    */
    server: {
        middlewareMode: true,
        port: parseInt(process.env.REACTIVATED_ORIGINAL_PORT ?? "0"),
        proxy: {
            [`^(?!${escapedBase}|${reactivatedEndpoint}).*`]: {
                target: `http://127.0.0.1:${process.env.REACTIVATED_DJANGO_PORT}/`,
            },
        },
    },
    appType: "custom",
    plugins: [react(), vanillaExtractPlugin(), 
    cjsInterop({
      // List of CJS dependencies that require interop
      dependencies: [
        "lz-string",
          "@reduxjs/toolkit",
          "immer",
          "lodash",
          "react-use",
          "react-helmet-async",
      ],
    }),
    ],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
    base,
};

export const vite = await createServer(rendererConfig);

app.use(vite.middlewares);
app.use(express.json());

app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    const {render} = (await vite.ssrLoadModule("reactivated/dist/render.mjs")) as {
        render: typeof renderType;
    };

    const {url, rendered} = await render(req, "development", "index");

    const transformed = await vite.transformIndexHtml(url, rendered);
    res.status(200).set({"Content-Type": "text/html"}).end(transformed);
});

app.listen(port, () => {
    console.log(`Server started at http://localhost:${port}`);
});
