import webpack from 'webpack';
import path from 'path';

import {Settings} from './models';

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
        },
        plugins: [
            new webpack.HotModuleReplacementPlugin(),
        ],
    }
};
