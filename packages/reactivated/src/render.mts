import {Request} from "express";
import React, {type JSX} from "react";
import ReactDOMServer from "react-dom/server";

// @ts-ignore
import {Provider} from "@reactivated";
// @ts-ignore
import {getTemplate} from "@reactivated/template";

import {PageShell} from "./shell";

export type Renderer<T = unknown> = (
    content: JSX.Element,
    req: {
        context: T;
        props: unknown;
    },
) => Promise<JSX.Element>;

const defaultRenderer: Renderer = (content) => Promise.resolve(content);

export const render = async (
    req: Request,
    vite: string,
    mode: "production" | "development",
    entryPoint: string,
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
            PageShell,
            {
                vite: vite,
                mode: mode,
                preloadContext: context,
                preloadProps: props,
                entryPoint: entryPoint,
            },
            React.createElement(
                Provider,
                {
                    value: context,
                },
                React.createElement(Template, props),
            ),
        ),
    );

    const html = ReactDOMServer.renderToString(
        await (customConfiguration?.default ?? defaultRenderer)(content, {
            context,
            props,
        }),
    );
    return `<!DOCTYPE html>\n${html}`;
};
