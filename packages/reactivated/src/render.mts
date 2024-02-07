import {Request} from "express";
import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";
import * as React from "react";
import * as ReactDOMServer from "react-dom/server";
import type {Options} from "./conf";

// @ts-ignore
import {Provider, viteGetTemplate as getTemplate} from "@reactivated";

export const renderPage = ({
    html,
    helmet,
    context,
    props,
    mode,
    entryPoint,
}: {
    html: string;
    helmet: HelmetServerState;
    context: any;
    props: any;
    mode: "production" | "development";
    entryPoint: string;
}) => {
    const scriptNonce = context.request.csp_nonce
        ? `nonce="${context.request.csp_nonce}"`
        : "";

    const css =
        mode == "production"
            ? `<link rel="stylesheet" type="text/css" href="/static/dist/${entryPoint}.css">`
            : "";
    const js =
        mode == "production"
            ? `<script src="/static/dist/${entryPoint}.js" defer crossOrigin="anonymous"></script>`
            : `<script type="module" src="/client/${entryPoint}.tsx"></script>`;

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
        ${css}

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
        ${js}
    </body>
</html>`;
};

const defaultConfiguration = {
    render: (content) => Promise.resolve(content),
} satisfies Options;

export type Renderer = (content: JSX.Element) => Promise<JSX.Element>;

export const render = async (
    req: Request,
    mode: "production" | "development",
    entryPoint: string,
) => {
    // @ts-ignore
    const customConfiguration: {default?: Render} | null = import.meta.glob(
        "@client/renderer.tsx",
        {eager: true},
    )["/client/renderer.tsx"];

    const {context, props} = req.body;
    const Template = getTemplate(context);
    const helmetContext = {} as FilledContext;

    const content = React.createElement(
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
    );

    const html = ReactDOMServer.renderToString(
        await (customConfiguration?.default ?? defaultConfiguration.render)(content),
    );
    const {helmet} = helmetContext;

    const rendered = renderPage({
        html,
        helmet,
        props,
        context,
        mode,
        entryPoint,
    });

    const url = context.request.path;
    return {url, rendered};
};
