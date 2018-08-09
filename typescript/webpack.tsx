import webpack from 'webpack';
import path from 'path';

const settings = require(path.resolve('./server/settings.json'));

const DJANGO_DEBUG_PORT = settings.DEBUG_PORT;
const NODE_DEBUG_PORT = DJANGO_DEBUG_PORT + 100;
const WEBPACK_DEBUG_PORT = DJANGO_DEBUG_PORT + 200;

export default {
    mode: 'development',
    entry: './client/app.tsx',
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
        filename: 'dist/bundle.js',
        publicPath: '/media/',
    },
    serve: {
        devMiddleware: {
            publicPath: '/media/',
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
                target: `http://localhost:${NODE_DEBUG_PORT}`,
            },
        },
    },
    plugins: [
        new webpack.HotModuleReplacementPlugin(),
    ],
}
