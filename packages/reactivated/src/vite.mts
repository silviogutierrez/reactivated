#!/usr/bin/env node

import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";
import {define} from "./conf.js";
import {SSRErrorResponse, serializeError} from "./errors.js";
import type {render as renderType} from "./render.mjs";
import {InlineConfig} from "vite";

// @ts-ignore
import {cjsInterop} from "vite-plugin-cjs-interop";

import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

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
        watch: {
            ignored: ["**/.venv/**", "**/capacitor/**"],
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

    try {
        const {render} = (await vite.ssrLoadModule("reactivated/dist/render.mjs")) as {
            render: typeof renderType;
        };

        const url = context.request.path;
        // For E2E tests, we may want to run them pointing to a running vite
        // instance for a quick feedback loop. Intead of the traditional python
        // manage.py build step necessary. So we ensure vite head always points
        // to the per-request STATIC_URL.
        const viteHead = (await vite.transformIndexHtml(url, "")).replaceAll(
            base,
            `${context.STATIC_URL}dist/`,
        );
        const rendered = await render(req, viteHead, "development", "index");

        res.status(200).set({"Content-Type": "text/html"}).end(rendered);
    } catch (error) {
        vite.ssrFixStacktrace(error as any);
        const errResp: SSRErrorResponse = {
            error: serializeError(error as any),
        };
        res.status(500).json(errResp);
    }
});
