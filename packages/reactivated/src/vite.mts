#!/usr/bin/env node

import React from "react";
import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";
import ReactDOMServer from "react-dom/server";
import {define} from "./conf.js";
import type {render as renderType} from "./render.mjs";
import type {Options} from "./conf";
import type {RendererConfig} from "./build.client.mjs";
import {resolveConfig, mergeConfig, loadConfigFromFile, InlineConfig} from "vite";

// @ts-ignore
import {cjsInterop} from "vite-plugin-cjs-interop";

import {Helmet, HelmetProvider, HelmetServerState} from "react-helmet-async";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

const isProduction = process.env.NODE_ENV === "production";
const port = process.env.REACTIVATED_VITE_PORT ?? 5173;
const base = process.env.BASE ?? "/";
const escapedBase = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const reactivatedEndpoint = "/_reactivated/".replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const app = express();

// Server goes first so we can pass it to HMR / Vite.
// Not sure if there are race conditions here but I doubt it.
const server = app.listen(port, () => {
    console.log("Reactivated vite process started\n");
});
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
        hmr: {
            server,
        },
    },
    define: define(),
    appType: "custom",
    plugins: [
        react(),
        vanillaExtractPlugin(),
        cjsInterop({
            // List of CJS dependencies that require interop
            dependencies: [
                "react-syntax-highlighter",
                "lz-string",
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
app.use(express.json({limit: "200mb"}));

app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    const {render} = (await vite.ssrLoadModule("reactivated/dist/render.mjs")) as {
        render: typeof renderType;
    };

    try {
        const url = context.request.path;
        const viteHead = await vite.transformIndexHtml(url, "");
        const rendered = await render(req, viteHead, "development", "index");

        res.status(200).set({"Content-Type": "text/html"}).end(rendered);
    } catch (error) {
        vite.ssrFixStacktrace(error as any);
        console.error(error);
        res.status(500).json({error: {}});
    }
});
