import React from 'react';
import axios from 'axios';
import webpack from 'webpack';
import express, {Request, Response} from 'express';
import ReactDOMServer from 'react-dom/server';
import middleware from 'webpack-dev-middleware';
import {IncomingMessage} from 'http';
import {getStyles} from 'typestyle';
import {compile} from 'json-schema-to-typescript'
import fs from 'fs';

import webpackConfig from '../webpack.config';

const compiler = webpack({
    ...webpackConfig,
    mode: 'development',
});
const proxy = require('express-http-proxy');

const app = express();

const index = `
<html>
    <script src="/bundle.js"></script>
    <body>

    </body>
</html>
`;

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
    <script src="/bundle.js"></script>
</body>
</html>
`;

const ssrProxy = proxy('localhost:8000', {
    userResHeaderDecorator(headers: Request['headers'], userReq: Request, userRes: Response, proxyReq: Request, proxyRes: IncomingMessage) {
        if (!('raw' in userReq.query) && proxyRes.headers['content-type'] === 'application/ssr+json') {
            headers['content-type'] = 'text/html; charset=utf-8';
        }

        return headers;
    },
    userResDecorator: (proxyRes: IncomingMessage, proxyResData: Buffer, userReq: Request, userRes: Response) => {
        if ('raw' in userReq.query || proxyRes.headers['content-type'] !== 'application/ssr+json') {
            return proxyResData;
        }

        const responseAsJSON: any = JSON.parse(proxyResData.toString('utf8'));
        const props = responseAsJSON;
        const Template = require(`../client/templates/${props.template_name}.tsx`).default;
        const rendered = ReactDOMServer.renderToString(<Template {...props} />);
        return renderPage({
            html: rendered,
            css: getStyles(),
            props,
        });
    },
});

const PATHS = [
    '/',
    '/form/',
]

export default {
    listen: async (port: number|string, callback?: () => void) => {
        const response = await axios.get('http://localhost:8000/schema/');
        const schema = response.data;
        const compiled = await compile(schema, schema.title)
        fs.writeFileSync("exports.tsx", compiled);

        /*
         * An example of a node-space route before we delegate to Django. Useful if we
         * need websockets etc.
        app.get('/', async (req, res) => {
            res.send('ok!');
        });
        */

        app.get('/schema/', async (req, res) => {
            const response = await axios.get('http://localhost:8000/schema/');
            const schema = response.data;
            const compiled = await compile(schema, schema.title)
            res.send(compiled);
        });

        app.use(middleware(compiler, {
            publicPath: '/',
        }));

        app.use(PATHS, ssrProxy);
        app.listen(port, callback);
    },
};
