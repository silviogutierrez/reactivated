import React from "react";
import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";
import ReactDOMServer from "react-dom/server";
import {render} from "./render.mjs";

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

const vite = await createServer({
    clearScreen: false,
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
    plugins: [react(), vanillaExtractPlugin()],
    resolve: {
        alias: {
            "@client": path.resolve(process.cwd(), "./client"),
            "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
    base,
});

app.use(vite.middlewares);
app.use(express.json());

app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    // @ts-ignore
    // const {Provider, getTemplate} = await import(path.resolve(process.cwd(), "./node_modules/_reactivated/index.tsx"));
    const {Provider, viteGetTemplate: getTemplate} = await vite.ssrLoadModule(
        "@reactivated/index.tsx",
    );

    const {url, rendered} = render(req, Provider, getTemplate, "development", "index");

    const transformed = await vite.transformIndexHtml(url, rendered);
    res.status(200).set({"Content-Type": "text/html"}).end(transformed);
});

app.listen(port, () => {
    console.log(`Server started at http://localhost:${port}`);
});
