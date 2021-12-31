import http from "http";
import ReactDOMServer from "react-dom/server";
import React from "react";
import {FilledContext, Helmet, HelmetData, HelmetProvider} from "react-helmet-async";
import fs from "fs";

import templates, {filenames} from './client/templates/**/*';

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

const PORT = 3000;

// Useful when running e2e tests or the like, where the output is not
// co-located with the running process.
// const REACTIVATED_CLIENT_ROOT = process.env.REACTIVATED_CLIENT_ROOT ?? `${process.cwd()}/client`;
const REACTIVATED_CLIENT_ROOT = process.env.REACTIVATED_CLIENT_ROOT ?? `./client`;

type Rendered = {
    status: "success",
    rendered: string;
} | {
    status: "error",
    error: unknown,
}

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

const render = (input: Buffer): Rendered => {
    const {context, props} = JSON.parse(input.toString("utf8"));
    const templatePath = `${REACTIVATED_CLIENT_ROOT}/templates/${context.template_name}.tsx`;
    const Template = templates.find((t, index) => filenames[index] === templatePath).default;
    const Component = Template;
    const helmetContext = {} as FilledContext;
    // const Provider = require(contextPath).Provider;

    const rendered = ReactDOMServer.renderToString(
        <HelmetProvider context={helmetContext}>
            {/* <Provider value={context}> */}
                <Template {...props} />
            {/*</Provider> */}
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
}

const server = http.createServer((req, res) => {
    let body = Buffer.from("");

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", () => {
        const payload = {
            props: {},
            context: {
                template_name: req.url.includes("Page") ? "Page.tsx" : "Login.tsx",
            },
        };
        body = Buffer.from(JSON.stringify(payload));
        const result = render(body);

        if (result.status === "success") {
            res.writeHead(OK_RESPONSE, {"Content-Type": "text/html; charset=utf-8"});
            res.end(result.rendered);
        } else {
            res.writeHead(ERROR_REPONSE, {"Content-Type": "application/json"});
            res.end(
                JSON.stringify(result.error, Object.getOwnPropertyNames(result.error)),
            );
        }
    });
});

/*
server.listen(PORT, () => {
    const address = server.address();

    if (typeof address === "string") {
        throw new Error();
    }
    process.stdout.write(`RENDERER:${address.port.toString()}:LISTENING`);
});
*/

const stdinBuffer = fs.readFileSync(0);
process.stdout.write(JSON.stringify(render(stdinBuffer)));
