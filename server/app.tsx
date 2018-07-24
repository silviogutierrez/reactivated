import React from 'react';
import axios from 'axios';
import webpack from 'webpack';
import path from 'path';
import express, {Request, Response} from 'express';
import ReactDOMServer from 'react-dom/server';
import middleware from 'webpack-dev-middleware';
import {getStyles} from 'typestyle';
import {compile} from 'json-schema-to-typescript'
import fs from 'fs';

import httpProxy, {ServerOptions} from 'http-proxy';

import webpackConfig from '../webpack.config';

const compiler = webpack({
    ...webpackConfig,
    mode: 'development',
});

const app = express();

export const renderPage = ({html, css, props}: {html: string, css: string, props: any}) => `
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <style id="styles-target">
        ${css}
    </style>
    <script>
        // WARNING: See the following for security issues around embedding JSON in HTML:
        // http://redux.js.org/recipes/ServerRendering.html#security-considerations
        window.__PRELOADED_STATE__ = ${JSON.stringify(props).replace(/</g, '\\u003c')}
    </script>
</head>
<body>
    <div id="root">${html}</div>
    <script src="/media/dist/bundle.js"></script>
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

export default {
    listen: async (options: ListenOptions, callback?: () => void) => {
        app.get('/schema/', async (req, res) => {
            const response = await axios.get('http://localhost:8000/schema/');
            const schema = response.data;
            const compiled = await compile(schema, schema.title)
            res.send(compiled);
        });

        /*
        app.use(middleware(compiler, {
            publicPath: '/',
        }));
        */

        const proxy = httpProxy.createProxyServer();

        proxy.on('proxyRes', (proxyRes, req, res) => {
            let body = Buffer.from('', 'utf8');

            proxyRes.on('data', function (data) {
                body = Buffer.concat([body, data as Buffer]);
            });
            proxyRes.on('end', function () {
                const response = body.toString('utf8');

                if ('raw' in (req as any).query || proxyRes.headers['content-type'] !== 'application/ssr+json') {
                    res.writeHead(proxyRes.statusCode!, proxyRes.headers)
                    res.end(response);
                }
                else {
                    const props = JSON.parse(response);
                    let body;

                    try {
                        const Template = require(`${process.cwd()}/client/templates/${props.template_name}.tsx`).default;
                        const rendered = ReactDOMServer.renderToString(<Template {...props} />);
                        const css = getStyles();

                        body = renderPage({
                            html: rendered,
                            css,
                            props,
                        });
                    }
                    catch (error) {
                        body = error.toString();
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
};
