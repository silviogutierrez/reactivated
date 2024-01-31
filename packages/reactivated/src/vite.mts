import React from "react";
import express from "express";
import path from "path";
import react from "@vitejs/plugin-react";

import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";

import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

const isProduction = process.env.NODE_ENV === "production";
const port = process.env.REACTIVATED_ORIGINAL_PORT || 5173;
const base = process.env.BASE || "/";
const escapedBase = base.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
const reactivatedEndpoint = "/_reactivated/".replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

const app = express();

const indexHTML = `
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React + TS</title>
    <!--app-head-->
  </head>
  <body>
    <div id="root"><!--app-html--></div>
    <script type="module" src="/client/entry-client.tsx"></script>
  </body>
</html>
`;

export const renderPage = ({
    html,
    helmet,
    context,
    props,
}: {
    html: string;
    helmet: HelmetServerState;
    context: any;
    props: any;
}) => {
    const scriptNonce = context.request.csp_nonce
        ? `nonce="${context.request.csp_nonce}"`
        : "";
    return `
<!DOCTYPE html>
<html ${helmet.htmlAttributes.toString()}>
    <head>
        <!--react-script-->
        <script ${scriptNonce}>
            // These go first because scripts below need them.
            // WARNING: See the following for security issues around embedding JSON in HTML:
            // http://redux.js.org/recipes/ServerRendering.html#security-considerations
            window.__PRELOADED_PROPS__ = ${JSON.stringify(props).replace(
                /</g,
                "\\u003c",
            )}
            window.__PRELOADED_CONTEXT__ = ${JSON.stringify(context).replace(
                /</g,
                "\\u003c",
            )}
        </script>

        ${helmet.base.toString()}
        ${helmet.link.toString()}
        ${helmet.meta.toString()}
        ${helmet.noscript.toString()}
        ${helmet.script.toString()}
        ${helmet.style.toString()}
        ${helmet.title.toString()}
    </head>
    <body ${helmet.bodyAttributes.toString()}>
        <div id="root">${html}</div>
        <script type="module" src="/client/index.tsx"></script>
    </body>
</html>`;
};

const {createServer} = await import("vite");

const vite = await createServer({
    clearScreen: false,
    server: {
        middlewareMode: true,
        port: parseInt(process.env.REACTIVATED_ORIGINAL_PORT ?? "0"),
        proxy: {
            [`^(?!${escapedBase}|${reactivatedEndpoint}).*`]: {
                target: `http://127.0.0.1:${process.env.REACTIVATED_BACKEND_PORT}/`,
            },
        },
    },
    // server: {middlewareMode: true, proxy: {
    //     /*
    //     "^.*": {
    //         target: "http://main.joyapp.com.silviogutierrez.localhost:12008/",
    //     },
    //     */
    //       // '^(?!\/$).+': {
    //           '^(?!\/$|\/@vite\/client$|\/client\/entry-client\.tsx$).+': {
    //           target: "http://main.joyapp.com.silviogutierrez.localhost:12008/",
    //         rewrite: (path) => {
    //             console.log(path);
    //             return path;
    //         },
    //       },
    // }},
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

import ReactDOMServer from "react-dom/server";

app.use("/_reactivated/", async (req, res) => {
    const {context, props} = req.body;

    // @ts-ignore
    // const {Provider, getTemplate} = await import(path.resolve(process.cwd(), "./node_modules/_reactivated/index.tsx"));
    const {Provider, viteGetTemplate: getTemplate} = await vite.ssrLoadModule(
        "@reactivated/index.tsx",
    );
    const Template = getTemplate(context);
    const helmetContext = {} as FilledContext;

    const html = ReactDOMServer.renderToString(
        React.createElement(
            React.StrictMode,
            {},
            React.createElement(
                HelmetProvider,
                {context: helmetContext},
                React.createElement(
                    Provider,
                    {value: context},
                    React.createElement(Template, props),
                ),
            ),
        ),
    );
    const {helmet} = helmetContext;

    const rendered = renderPage({
        html,
        helmet,
        props,
        context,
    });

    const url = context.request.path;
    const transformed = await vite.transformIndexHtml(url, rendered);
    const withReact = transformed.replace(
        "<!--react-script-->",
        `
        <script type="module">
          import RefreshRuntime from '${base}@react-refresh'
          RefreshRuntime.injectIntoGlobalHook(window)
          window.$RefreshReg$ = () => {}
          window.$RefreshSig$ = () => (type) => type
          window.__vite_plugin_react_preamble_installed__ = true
        </script>
    `,
    );

    // res.status(200).set({"Content-Type": "text/html"}).end("thispingingisworking");
    // res.status(200).set({"Content-Type": "text/html"}).end("hello");
    res.status(200).set({"Content-Type": "text/html"}).end(transformed);
});

app.listen(port, () => {
    console.log(`Server started at http://localhost:${port}`);
});
