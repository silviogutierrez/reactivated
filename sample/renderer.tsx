import * as React from "react";
import * as ReactDOMServer from "react-dom/server";
import type {Options} from "reactivated/dist/conf";

import * as http from "http";
import * as fs from "fs";

import {
    FilledContext,
    Helmet,
    HelmetProvider,
    HelmetServerState,
} from "react-helmet-async";

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

    const customConfiguration = null;
    const defaultConfiguration = {
        render: (content) => Promise.resolve(content),
    } satisfies Options;

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
}

export const serverRender = (body: Buffer) => {
    const {context, props} = JSON.parse(body.toString("utf8"));
    return render({context, props});
};

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

// @ts-ignore
import {Provider, viteGetTemplate as getTemplate} from "@reactivated";

// Relative path to keep it under 100 characters.
// See: https://unix.stackexchange.com/questions/367008/why-is-socket-path-length-limited-to-a-hundred-chars
export const SOCKET_PATH =
    process.env.REACTIVATED_SOCKET ?? `node_modules/_reactivated/reactivated.sock`;

export const server = http.createServer((req, res) => {
    console.log(getTemplate)
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
