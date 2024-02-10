import React from "react";
import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";
import ReactDOMServer from "react-dom/server";
import {render} from "./render.mjs";

import {Helmet, HelmetProvider, HelmetServerState} from "react-helmet-async";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

// @ts-ignore
import {Provider, getTemplate} from "@reactivated";

const isProduction = process.env.NODE_ENV === "production";
const port = process.env.REACTIVATED_VITE_PORT || 5173;
const base = process.env.BASE || "/";
const escapedBase = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const reactivatedEndpoint = "/_reactivated/".replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const app = express();

app.use(express.json({limit: "200mb"}));
app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    const {url, rendered} = await render(req, "production", "index");
    res.status(200).set({"Content-Type": "text/html"}).end(rendered);
});

app.listen(port, () => {
    process.stdout.write(`RENDERER:http://localhost:${port}:LISTENING`);
});
