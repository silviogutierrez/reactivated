import { Request } from "express";
import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";
import * as React from "react";
import * as ReactDOMServer from "react-dom/server";
import type {Options} from "./conf";

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

export const render = (req: Request, Provider: any, getTemplate: any) => {
    const {context, props} = req.body;
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
    return {url, rendered};
}
