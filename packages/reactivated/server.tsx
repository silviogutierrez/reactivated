import React from 'react';
import webpack from 'webpack';
import path from 'path';
import express, {Request, Response} from 'express';
import ReactDOMServer from 'react-dom/server';
import Helmet, {HelmetData} from 'react-helmet';
import {getStyles} from 'typestyle';
import {compile} from 'json-schema-to-typescript'
import fs from 'fs';

import httpProxy, {ServerOptions} from 'http-proxy';

import {Settings} from './models';
import {Provider} from './context';

const app = express();

export const bindRenderPage = (settings: Settings) => ({html, helmet, css, context, props}: {html: string, helmet: HelmetData, css: string, context: any, props: any}) => `
<!DOCTYPE html>
<html>
    <head ${helmet.htmlAttributes.toString()}>
        ${helmet.title.toString()}
        ${helmet.meta.toString()}
        ${helmet.link.toString()}
        <style id="styles-target">
            ${css}
        </style>
        <script>
            // WARNING: See the following for security issues around embedding JSON in HTML:
            // http://redux.js.org/recipes/ServerRendering.html#security-considerations
            window.__PRELOADED_PROPS__ = ${JSON.stringify(props).replace(/</g, '\\u003c')}
            window.__PRELOADED_CONTEXT__ = ${JSON.stringify(context).replace(/</g, '\\u003c')}
        </script>
        <link rel="shortcut icon" href="${settings.STATIC_URL}css/images/favicon.ico" type="image/x-icon" />
    </head>
    <body ${helmet.bodyAttributes.toString()}>
        <div id="root">${html}</div>
        <script src="${settings.MEDIA_URL}dist/bundle.js"></script>
    </body>
</html>
`;

const PATHS = [
    '/',
    '/form/',
]

interface ListenOptions {
    node: number|string;
    django: number|string;
}

export default (settings: Settings) => ({

    listen: async (options: ListenOptions, callback?: () => void) => {
        const renderPage = bindRenderPage(settings);
        const proxy = httpProxy.createProxyServer();

        proxy.on('proxyRes', (proxyRes, req, res) => {
            let body = Buffer.from('') //, 'utf8');

            proxyRes.on('data', function (data) {
                body = Buffer.concat([body, data as Buffer]);
            });
            proxyRes.on('end', function () {
                const response = body // .toString('utf8');

                if ('raw' in (req as any).query || proxyRes.headers['content-type'] !== 'application/ssr+json') {
                    res.writeHead(proxyRes.statusCode!, proxyRes.headers)
                    res.end(response);
                }
                else {
                    let body;

                    try {
                        const {context, props} = JSON.parse(response.toString('utf8'));
                        const template_path = `${process.cwd()}/client/templates/${context.template_name}.tsx`;

                        // TODO: disable this in production.
                        if (process.env.NODE_ENV !== 'production') {
                            delete require.cache[template_path];
                        }

                        const Template = require(template_path).default;
                        const rendered = ReactDOMServer.renderToString(<Provider value={context}><Template {...props} /></Provider>);
                        const helmet = Helmet.renderStatic();
                        const css = getStyles();

                        body = renderPage({
                            html: rendered,
                            helmet,
                            css,
                            props,
                            context,
                        });
                    }
                    catch (error) {
                        body = error.stack;
                    }

                    res.writeHead(proxyRes.statusCode!, {
                        ...proxyRes.headers,
                        'Content-Type': 'text/html; charset=utf-8',
                        'Content-Length': Buffer.byteLength(body),
                    });
                    res.end(body);
                }

            });
        });

        const target = typeof options.django == 'number' ? `http://localhost:${options.django}` : {
            socketPath: options.django,
        } as ServerOptions['target'];

        app.use(PATHS, (req, res, next) => {
            proxy.web(req, res, {
                // Change origin cannot be used with sockets.
                // changeOrigin: true,
                selfHandleResponse: true,
                target,
            });
        });
        app.listen(options.node, callback);
    },
});
