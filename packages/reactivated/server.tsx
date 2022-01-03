import fs from "fs";
import {compile} from "json-schema-to-typescript";
import path from "path";
import React from "react";
import ReactDOMServer from "react-dom/server";
import {FilledContext, Helmet, HelmetData, HelmetProvider} from "react-helmet-async";

// Useful when running e2e tests or the like, where the output is not
// co-located with the running process.
const REACTIVATED_CLIENT_ROOT =
    process.env.REACTIVATED_CLIENT_ROOT ?? `../client`;

import {Settings} from "./models";

// TODO: WHAT DOES THIS NEED TO BE? Even 100k was super fragile and a 10 choice field broke it.
export const BODY_SIZE_LIMIT = "100000000k";

export const renderPage = ({
        html,
        helmet,
        context,
        props,
    }: {
        html: string;
        helmet: HelmetData;
        context: any;
        props: any;
    }) =>
        `
<!DOCTYPE html>
<html>
    <head ${helmet.htmlAttributes.toString()}>
        <script>
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
    </body>
</html>
`;

const PATHS = ["/", "/form/"];

type Result =
    | {
          status: "success";
          rendered: string;
      }
    | {
          status: "error";
          error: any;
      };

export const render = (
    {context, props}: {context: any, props: any},
    Provider: React.ComponentType<any>,
    Template: React.ComponentType<any>,
): Result => {
    try {
        const helmetContext = {} as FilledContext;

        const rendered = ReactDOMServer.renderToString(
            <HelmetProvider context={helmetContext}>
                <Provider value={context}>
                    <Template {...props} />
                </Provider>
            </HelmetProvider>,
        );

        const {helmet} = helmetContext;

        return {
            status: "success",
            rendered: renderPage({
                html: rendered,
                helmet,
                props,
                context,
            }),
        };
    } catch (error) {
        return {status: "error", error};
    }
};

export const simpleRender = () => {
    const input = fs.readFileSync(0);
    const {context, props} = JSON.parse(input.toString("utf8"));
    const {Provider, getTemplate} = require("../../client/generated");
    const Template = getTemplate(context);

    process.stdout.write(JSON.stringify(render({context, props}, Provider, Template)));
}

interface ListenOptions {
    node: number | string;
    django: number | string;
}
