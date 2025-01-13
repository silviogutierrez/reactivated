import {Request} from "express";
import React, {type JSX} from "react";
import {Response} from "express";
import ReactDOMServer from "react-dom/server";
import {renderToPipeableStream} from "react-dom/server";
import {Transform} from "node:stream";

import {SSRErrorResponse, serializeError} from "./errors.js";
// @ts-ignore
import {Provider} from "@reactivated";
// @ts-ignore
import {getTemplate} from "@reactivated/template";

export type Renderer<T = unknown> = (
    content: JSX.Element,
    req: {
        context: T;
        props: unknown;
    },
) => Promise<JSX.Element>;

const defaultRenderer: Renderer = (content) => Promise.resolve(content);

function serJSON(data: unknown): string {
    return JSON.stringify(data).replace(/</g, "\\u003c");
}

export const render = async (
    req: Request,
    res: Response,
    vite: string,
    mode: "production" | "development",
    entryPoint: string,
    ssrFixStacktrace?: (error: Error) => void,
) => {
    // @ts-ignore
    const customConfiguration: {default?: Renderer} | null = import.meta.glob(
        "@client/renderer.tsx",
        {eager: true},
    )["/client/renderer.tsx"];

    const {context, props} = req.body;
    const Template = await getTemplate(context);
    const scriptNonce = context.request.csp_nonce ?? undefined;

    const {STATIC_URL} = context;

    if (STATIC_URL == null) {
        console.error("Ensure your context processor includes STATIC_URL");
    }
    const css =
        mode == "production"
            ? `<link rel="stylesheet" type="text/css" href="${STATIC_URL}dist/${entryPoint}.css">`
            : "";
    const js =
        mode == "production"
            ? `<script type="module" src="${STATIC_URL}dist/${entryPoint}.js" defer crossOrigin="anonymous"></script>`
            : `<script type="module" src="${STATIC_URL}dist/client/${entryPoint}.tsx"></script>`;

    const content = React.createElement(
        React.StrictMode,
        {},
        React.createElement(
            Provider,
            {value: context},
            React.createElement(Template, props),
        ),
    );

    let hasError = false;

    const {pipe} = renderToPipeableStream(
        await (customConfiguration?.default ?? defaultRenderer)(content, {
            context,
            props,
        }),

        {
            nonce: scriptNonce,
            bootstrapScriptContent: `
        window.__PRELOADED_PROPS__ = ${serJSON(props)};
        window.__PRELOADED_CONTEXT__ = ${serJSON(context)};
        `,
            onError(error) {
                hasError = true;
                if (ssrFixStacktrace) {
                    console.log("fixing stacktrace");
                    ssrFixStacktrace(error as any);
                }
                const errResp: SSRErrorResponse = {
                    error: serializeError(error as any),
                };
                res.status(500).json(errResp);
            },
            onAllReady() {
                if (hasError) {
                    return;
                }
                res.status(200);
                // Seems like the renderer.py, at least for unix socket, requires a charset
                // unlike the React docs
                res.setHeader("content-type", "text/html; charset=utf-8");
                const transformStream = new Transform({
                    transform(chunk, encoding, callback) {
                        res.write(chunk, encoding);
                        callback();
                    },
                });
                transformStream.on("finish", () => {
                    res.end(vite + css + js);
                });

                pipe(transformStream);
            },
        },
    );
};
