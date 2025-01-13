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

    const content = React.createElement(
        React.StrictMode,
        {},
        React.createElement(
            App,
        ),
    );

    const {STATIC_URL} = context;

    if (STATIC_URL == null) {
        console.error("Ensure your context processor includes STATIC_URL");
    }

    const script =
        props.mode == "production"
            ? `${STATIC_URL}dist/${entryPoint}.js`
            : `${STATIC_URL}dist/client/${entryPoint}.tsx`;

    const preamble = `
    <script type="module">
import RefreshRuntime from "/static/dist/@react-refresh"
RefreshRuntime.injectIntoGlobalHook(window)
window.$RefreshReg$ = () => {}
window.$RefreshSig$ = () => (type) => type
window.__vite_plugin_react_preamble_installed__ = true
</script>
`;


    console.log(vite);
    const {pipe} = renderToPipeableStream(content, {
        // bootstrapScriptContent: `
        // window.__PRELOADED_PROPS__ = ${serJSON(props)};
        // window.__PRELOADED_CONTEXT__ = ${serJSON(context)};
        // `,
        bootstrapModules: ["/static/dist/@vite/client", script],
        onShellReady() {
            res.setHeader("content-type", "text/html");
            const transformStream = new Transform({
                transform(chunk, encoding, callback) {
                    res.write(chunk, encoding);
                    callback();
                },
            });

            // const [htmlStart, htmlEnd] = template.split(`<!--app-html-->`)

            transformStream.on("finish", () => {
                // res.end("")
                res.end(vite);
                // res.end(htmlEnd)
            });

            pipe(transformStream);
        },
    });

    /*

    const html = ReactDOMServer.renderToString(
        await (customConfiguration?.default ?? defaultRenderer)(content, {
            context,
            props,
        }),
    );
    return `<!DOCTYPE html>\n${html}`;
    */
};
