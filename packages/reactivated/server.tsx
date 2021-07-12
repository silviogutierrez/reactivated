import fs from "fs";
import {compile} from "json-schema-to-typescript";
import path from "path";
import React from "react";
import ReactDOMServer from "react-dom/server";
import {FilledContext, Helmet, HelmetData, HelmetProvider} from "react-helmet-async";
import webpack from "webpack";

import moduleAlias from "module-alias";

// Useful when running e2e tests or the like, where the output is not
// co-located with the running process.
const REACTIVATED_CLIENT_ROOT =
    process.env.REACTIVATED_CLIENT_ROOT ?? `${process.cwd()}/client`;

moduleAlias.addAlias("@client", REACTIVATED_CLIENT_ROOT);

import httpProxy, {ServerOptions} from "http-proxy";

// import {Provider} from "./context";
import {Settings} from "./models";

// TODO: WHAT DOES THIS NEED TO BE? Even 100k was super fragile and a 10 choice field broke it.
export const BODY_SIZE_LIMIT = "100000000k";

export const bindRenderPage = (settings: Settings) => ({
    html,
    helmet,
    context,
    props,
}: {
    html: string;
    helmet: HelmetData;
    context: any;
    props: any;
}) => `
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

const defaultRenderPage = bindRenderPage({
    DEBUG: true,
    DEBUG_PORT: 200,
    MEDIA_URL: "/media/",
    STATIC_URL: "/static/",
});

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
    input: Buffer,
    renderPage: typeof defaultRenderPage = defaultRenderPage,
): Result => {
    const {context, props} = JSON.parse(input.toString("utf8"));

    const templatePath = `${REACTIVATED_CLIENT_ROOT}/templates/${context.template_name}`;
    const contextPath = `${REACTIVATED_CLIENT_ROOT}/generated`;

    if (process.env.NODE_ENV !== "production") {
        // Our template names have no extension by design, for when we transpile.
        delete require.cache[`${templatePath}.tsx`];
        delete require.cache[`${templatePath}.jsx`];

        // When a template includes other components, like Layout, we also want
        // to clear that cache. Right now, I'm not sure what actually needs to
        // be cleared. Layout.tsx is not in the cache. Maybe it's cached by
        // way of another module.
        //
        // So we clear *everything* except:
        //
        // Context stateful and we need them for the initial page.
        //
        // react-helmet-async has a context that also cannot be cleared. You'll
        // get a cryptic 404 for this route.
        //
        // mini-css-extract-plugin breaks when hot reloading if cleared.
        //
        // Possible better fix: https://stackoverflow.com/a/14801711
        for (const cacheKey of Object.keys(require.cache)) {
            if (
                !cacheKey.includes("reactivated/context") &&
                !cacheKey.includes("mini-css-extract-plugin") &&
                !cacheKey.includes("react-helmet-async") &&
                // If we delete React from the cache, this creates two duplicate
                // instances of React and we get server side rendering issues
                // when using hooks.
                // https://reactjs.org/warnings/invalid-hook-call-warning.html
                //
                // Note the trailing slash so to avoid matching reactivated.
                !cacheKey.includes("react/")
            ) {
                delete require.cache[cacheKey];
            }
        }

        // When developing reactivated itself locally, including Widget.tsx etc.
        // TODO: has a bug with context.
        // for (const cacheKey of Object.keys(require.cache)) {
        //     if (cacheKey.includes('reactivated/dist')) {
        //         delete require.cache[cacheKey];
        //     }
        // }
    }

    try {
        const helmetContext = {} as FilledContext;
        const Template = require(templatePath).default;
        const Provider = require(contextPath).Context.Provider;

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

interface ListenOptions {
    node: number | string;
    django: number | string;
}
