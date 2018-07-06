import React from 'react';
import axios from 'axios';
import express, {Request, Response} from 'express';
import ReactDOMServer from 'react-dom/server';
import {IncomingMessage} from 'http';

const proxy = require('express-http-proxy');

const app = express();

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
        const {template_name, props} = responseAsJSON;
        const Template = require(`./templates/${template_name}.tsx`).default;
        const rendered = ReactDOMServer.renderToString(<Template {...props} />);
        return rendered;
    },
});

const PATHS = [
    '/',
    '/form/',
]

/*
 * An example of a node-space route before we delegate to Django. Useful if we
 * need websockets etc.
app.get('/', async (req, res) => {
    res.send('ok!');
});
*/

app.use(PATHS, ssrProxy);

app.listen(3000, () => console.log('Example app listening on port 3000!'));
