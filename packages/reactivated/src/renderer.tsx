import fs from "fs";
import http from "http";
import {compile} from "json-schema-to-typescript";
import path from "path";
import React from "react";
import ReactDOMServer from "react-dom/server";
import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";

import {Options} from "./conf";
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
    </body>
</html>`;
};

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

export const render = async ({
    context,
    props,
}: {
    context: any;
    props: any;
}): Promise<Result> => {
    const defaultConfiguration = {
        render: (content) => Promise.resolve(content),
    } satisfies Options;

    let customConfiguration: {default?: Options} | null = null;

    try {
        customConfiguration = await import(
            // @ts-ignore
            "_reactivated/conf.mjs"
        );
    } catch (error: unknown) {}

    // @ts-ignore
    const {Provider, getTemplate} = await import("_reactivated/index.tsx");

    try {
        const Template = getTemplate(context);
        const helmetContext = {} as FilledContext;

        const content = (
            <HelmetProvider context={helmetContext}>
                <Provider value={context}>
                    <Template {...props} />
                </Provider>
            </HelmetProvider>
        );

        const rendered = ReactDOMServer.renderToString(
            await (customConfiguration?.default?.render ?? defaultConfiguration.render)(
                content,
            ),
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

        return {
            status: "success",
            rendered,
        };
    } catch (error) {
        return {status: "error", error};
    }
};

export const simpleRender = () => {
    const input = fs.readFileSync(0);
    const {context, props} = JSON.parse(input.toString("utf8"));

    process.stdout.write(JSON.stringify(render({context, props})));
};

export const serverRender = (body: Buffer) => {
    const {context, props} = JSON.parse(body.toString("utf8"));
    return render({context, props});
};

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

// Relative path to keep it under 100 characters.
// See: https://unix.stackexchange.com/questions/367008/why-is-socket-path-length-limited-to-a-hundred-chars
export const SOCKET_PATH =
    process.env.REACTIVATED_SOCKET ?? `node_modules/_reactivated/reactivated.sock`;

export const server = http.createServer((req, res) => {
    let body = Buffer.from("");

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", async () => {
        const result = await serverRender(body);

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

if (fs.existsSync(SOCKET_PATH)) {
    fs.unlinkSync(SOCKET_PATH);
}

server.listen(SOCKET_PATH, () => {
    const address = server.address();

    if (address == null) {
        throw new Error();
    } else if (typeof address === "string") {
        process.stdout.write(`RENDERER:${address}:LISTENING`);
    } else {
        process.stdout.write(`RENDERER:${address.port.toString()}:LISTENING`);
    }
});
