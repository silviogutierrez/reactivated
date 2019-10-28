import {resetIdCounter} from "downshift";
import express, {Request, Response} from "express";
import fs from "fs";
import {compile} from "json-schema-to-typescript";
import path from "path";
import React from "react";
import ReactDOMServer from "react-dom/server";
import Helmet, {HelmetData} from "react-helmet";
import {getStyles} from "typestyle";
import webpack from "webpack";

import moduleAlias from "module-alias";
moduleAlias.addAlias("@client", `${process.cwd()}/client`);

import httpProxy, {ServerOptions} from "http-proxy";

import {Provider} from "./context";
import {Settings} from "./models";

// TODO: WHAT DOES THIS NEED TO BE? Even 100k was super fragile and a 10 choice field broke it.
export const BODY_SIZE_LIMIT = "100000000k";

const app = express();

export const bindRenderPage = (settings: Settings) => ({
    html,
    helmet,
    css,
    context,
    props,
}: {
    html: string;
    helmet: HelmetData;
    css: string;
    context: any;
    props: any;
}) => `
<!DOCTYPE html>
<html>
    <head ${helmet.htmlAttributes.toString()}>
        ${helmet.base.toString()}
        ${helmet.link.toString()}
        ${helmet.meta.toString()}
        ${helmet.noscript.toString()}
        ${helmet.script.toString()}
        ${helmet.style.toString()}
        ${helmet.title.toString()}
        <style id="styles-target">
            ${css}
        </style>
        <script>
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
        <link rel="shortcut icon" href="${
            settings.STATIC_URL
        }css/images/favicon.ico" type="image/x-icon" />
    </head>
    <body ${helmet.bodyAttributes.toString()}>
        <div id="root">${html}</div>
        <script src="${settings.MEDIA_URL}dist/bundle.js"></script>
    </body>
</html>
`;

const PATHS = ["/", "/form/"];

const defaultRenderPage = bindRenderPage({
    DEBUG: true,
    DEBUG_PORT: 200,
    MEDIA_URL: "/media/",
    STATIC_URL: "/static/",
});

export const render = (
    input: Buffer,
    renderPage: typeof defaultRenderPage = defaultRenderPage,
) => {
    const {context, props} = JSON.parse(input.toString("utf8"));

    const templatePath = `${process.cwd()}/client/templates/${context.template_name}`;

    // TODO: disable this in production.
    if (process.env.NODE_ENV !== "production") {
        // Our template names have no extension by design, for when we transpile.
        delete require.cache[`${templatePath}.tsx`];
        delete require.cache[`${templatePath}.jsx`];

        // When a template includes other components, like Layout, we also want
        // to clear that cache. Right now, I'm not sure what actually needs to
        // be cleared. Layout.tsx is not in the cache. Maybe it's cached by
        // way of another module.
        //
        // So we clear *everything* except context, typestyle and helmet because those
        // are stateful and we need them for the initial page.
        //
        // Possible better fix: https://stackoverflow.com/a/14801711
        for (const cacheKey of Object.keys(require.cache)) {
            if (
                !cacheKey.includes("reactivated/context") &&
                !cacheKey.includes("typestyle") &&
                !cacheKey.includes("helmet")
            ) {
                delete require.cache[cacheKey];
            }
        }

        // When developing reactivated itself locally, including Widget.tsx etc.
        // TODO: has a bug with context.
        // for (const cacheKey of Object.keys(require.cache)) {
        //     if (cacheKey.includes('reactivated/dist')) {
        //         delete require.cache[cacheKey];
        //     }
        // }
    }

    const Template = require(templatePath).default;
    // See https://github.com/downshift-js/downshift#resetidcounter
    resetIdCounter();
    const rendered = ReactDOMServer.renderToString(
        <Provider value={context}>
            <Template {...props} />
        </Provider>,
    );
    const helmet = Helmet.renderStatic();
    const css = getStyles();

    return renderPage({
        html: rendered,
        helmet,
        css,
        props,
        context,
    });
};

interface ListenOptions {
    node: number | string;
    django: number | string;
}

export default (settings: Settings) => ({
    listen: async (options: ListenOptions, callback?: () => void) => {
        const renderPage = bindRenderPage(settings);
        const proxy = httpProxy.createProxyServer();

        proxy.on("proxyRes", (proxyRes, req, res) => {
            let body = Buffer.from(""); // , 'utf8');

            proxyRes.on("data", data => {
                body = Buffer.concat([body, data as Buffer]);
            });
            proxyRes.on("end", () => {
                const response = body; // .toString('utf8');

                // console.log(req.headers);
                // console.log('first', req.headers['x-requested-with']);
                // console.log('second', req.headers['X-Requested-With']);
                // console.log('third', req.headers['Accept']);
                // console.log('fourth', req.headers['accept']);
                const isAjax = req.headers["x-requested-with"] === "XMLHttpRequest";

                if (
                    isAjax === true ||
                    "raw" in (req as any).query ||
                    proxyRes.headers["content-type"] !== "application/ssr+json"
                ) {
                    res.writeHead(proxyRes.statusCode!, proxyRes.headers);
                    res.end(response);
                } else {
                    let content;

                    try {
                        content = render(response, renderPage);
                    } catch (error) {
                        content = error.stack;
                    }

                    res.writeHead(proxyRes.statusCode!, {
                        ...proxyRes.headers,
                        "Content-Type": "text/html; charset=utf-8",
                        "Content-Length": Buffer.byteLength(content),
                    });
                    res.end(content);
                }
            });
        });

        const target =
            typeof options.django === "number"
                ? `http://localhost:${options.django}`
                : ({
                      socketPath: options.django,
                  } as ServerOptions["target"]);

        app.use(PATHS, (req, res, next) => {
            proxy.web(req, res, {
                // Change origin cannot be used with sockets.
                // changeOrigin: true,
                selfHandleResponse: true,
                target,
            });
        });
        app.listen(options.node, callback);
    },
});
