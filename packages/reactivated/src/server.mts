import React from "react";
import express from "express";
import path from "node:path";
import http from "node:http";
import os from "node:os";
import react from "@vitejs/plugin-react";
import ReactDOMServer from "react-dom/server";
import {SSRErrorResponse, serializeError} from "./errors.js";
import {render} from "./render.mjs";

import {Helmet, HelmetProvider, HelmetServerState} from "react-helmet-async";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

// @ts-ignore
import {Provider, getTemplate} from "@reactivated";

const isProduction = process.env.NODE_ENV === "production";
const socketPath = path.join(os.tmpdir(), `reactivated.${process.pid}.sock`);
const base = process.env.BASE || "/";
const escapedBase = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const reactivatedEndpoint = "/_reactivated/".replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const app = express();

app.use(express.json({limit: "200mb"}));
app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    try {
        const rendered = await render(req, "", "production", "index");
        res.status(200).set({"Content-Type": "text/html"}).end(rendered);
    } catch (error) {
        const errResp: SSRErrorResponse = {
            error: serializeError(error as any),
        };
        res.status(500).json(errResp);
    }
});

const server = http.createServer(app);
server.listen(socketPath, () => {
    process.stdout.write(`RENDERER:${socketPath}:LISTENING`);
});

process.on("SIGTERM", () => {
    server.close();
});
