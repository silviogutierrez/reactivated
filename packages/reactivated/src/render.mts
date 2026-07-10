import {Request} from "express";
import React, {type JSX} from "react";
import {Response} from "express";
import {renderToPipeableStream} from "react-dom/server";
import {preinit} from "react-dom";
import {Transform} from "node:stream";

import {SSRErrorResponse, serializeError} from "./errors.js";
import {getReactivateConfig} from "./client.js";
// @ts-ignore
import {Provider} from "@reactivated";
// @ts-ignore
import {getTemplate} from "virtual:reactivated/templates";

// Evaluate the app entry, if one exists, for its side effect: reactivate()
// registers the app config (read below via getReactivateConfig). The entry
// runs in the SSR module graph, so its module scope must be node-safe;
// browser-only setup belongs inside init, which never runs here.
// @ts-ignore
const entryModules = import.meta.glob("@client/index.tsx", {eager: true});
export const appHasEntryFile = Object.keys(entryModules).length > 0;

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
    const {context, props, entry_point: requestEntryPoint} = req.body;
    const Template = await getTemplate(context);
    const scriptNonce = context.request.csp_nonce ?? undefined;
    const resolvedEntryPoint = requestEntryPoint ?? entryPoint;

    const {STATIC_URL} = context;

    if (STATIC_URL == null) {
        console.error("Ensure your context processor includes STATIC_URL");
    }

    // CSS must be loaded via preinit INSIDE a component (during render)
    // JS is loaded via bootstrapModules in renderToPipeableStream options
    const CSSLoader: React.FC<React.PropsWithChildren> = ({children}) => {
        if (mode === "production") {
            preinit(
                `${STATIC_URL}dist/${resolvedEntryPoint}.css?v=${process.env.RELEASE_VERSION ?? ""}`,
                {as: "style"},
            );
        }
        return children;
    };

    const content = React.createElement(
        React.StrictMode,
        null,
        React.createElement(
            CSSLoader,
            null,
            React.createElement(
                Provider,
                {value: context},
                React.createElement(Template, props),
            ),
        ),
    );

    let hasError = false;

    const config = getReactivateConfig();
    const wrapped = config.render
        ? await config.render(content, {ssr: true, context, props})
        : content;

    const {pipe} = renderToPipeableStream(
        wrapped,

        {
            nonce: scriptNonce,
            bootstrapScriptContent: `
        window.__PRELOADED_PROPS__ = ${serJSON(props)};
        window.__PRELOADED_CONTEXT__ = ${serJSON(context)};
        `,
            bootstrapModules:
                mode === "production"
                    ? [
                          `${STATIC_URL}dist/${resolvedEntryPoint}.js?v=${process.env.RELEASE_VERSION ?? ""}`,
                      ]
                    : resolvedEntryPoint === "index" && !appHasEntryFile
                      ? [`${STATIC_URL}dist/@id/virtual:reactivated/entry`]
                      : [`${STATIC_URL}dist/client/${resolvedEntryPoint}.tsx`],
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
                    res.end(vite);
                });

                pipe(transformStream);
            },
        },
    );
};
