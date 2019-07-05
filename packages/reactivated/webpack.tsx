import webpack from 'webpack';
import path from 'path';

import express, {Application} from 'express';

import {Settings} from './models';
import {render} from './server';


export const createConfig = (settings: Settings) => {
    const DJANGO_DEBUG_PORT = settings.DEBUG_PORT;
    const NODE_DEBUG_PORT = DJANGO_DEBUG_PORT + 100;
    const WEBPACK_DEBUG_PORT = DJANGO_DEBUG_PORT + 200;

    return {
        mode: 'development',
        entry: './client/index.tsx',
        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    loader: 'awesome-typescript-loader'
                }
            ]
        },
        resolve: {
            modules: [
                path.resolve('./'), 'node_modules',
            ],
            extensions: [ '.tsx', '.ts', '.js' ],
            symlinks: false,
        },
        output: {
            filename: 'bundle.js',
            publicPath: `${settings.MEDIA_URL}dist/`,
        },
        serve: {
            devMiddleware: {
                publicPath: `${settings.MEDIA_URL}dist/`,
            },
        },

        devServer: {
            disableHostCheck: true,
            hot: true,
            inline: true,
            progress: true,
            port: WEBPACK_DEBUG_PORT,
            proxy: {
                '**': {
                    target: `http://localhost:${DJANGO_DEBUG_PORT}`,
                },
            },
            before: (app: Application) => {
                app.use(express.json())
                app.post('/__ssr/', (req, res) => {
                    const rendered = render(Buffer.from(JSON.stringify(req.body)));
                    res.json({rendered});
                });
            },
        },
        // Docs say to put this in.
        // But others say to leave it out. Currently, HMR only works if left out.
        // plugins: [
        //     new webpack.HotModuleReplacementPlugin(),
        // ],
    }
};
