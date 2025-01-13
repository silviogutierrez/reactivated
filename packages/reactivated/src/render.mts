import {Request} from "express";
import React, {type JSX} from "react";
import {Response} from "express";
import ReactDOMServer from "react-dom/server";
import {renderToPipeableStream} from "react-dom/server";
import {Transform} from "node:stream";

// @ts-ignore
import {Provider} from "@reactivated";
// @ts-ignore
import {getTemplate} from "@reactivated/template";

import {PageShell, App} from "./shell";

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
    vite: string,
    mode: "production" | "development",
    entryPoint: string,
    res: Response,
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
        Provider,
        {value: context},
        React.createElement(Template),
    );

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
            onShellReady() {
                res.setHeader("content-type", "text/html");
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
