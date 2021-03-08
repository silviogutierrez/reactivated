import path from "path";
import webpack from "webpack";

import {Settings} from "./models";
import {BODY_SIZE_LIMIT, render} from "./server";

const WEBPACK_PORT_PADDING = 200;

export const createConfig = (settings: Settings) => {
    const DJANGO_DEBUG_PORT = settings.DEBUG_PORT;
    const WEBPACK_DEBUG_PORT = DJANGO_DEBUG_PORT + WEBPACK_PORT_PADDING;

    return {
        mode: "development",
        entry: "./client/index.tsx",
        module: {
            rules: [
                {
                    test: /\.tsx?$/,
                    loader: "awesome-typescript-loader",
                },
            ],
        },
        resolve: {
            alias: {
                "@client": path.resolve(process.cwd(), "client/"),
            },
            modules: [path.resolve("./"), "node_modules"],
            extensions: [".tsx", ".ts", ".js"],
            symlinks: false,
        },
        output: {
            filename: "bundle.js",
            publicPath: `${settings.STATIC_URL}dist/`,
        },
        serve: {
            devMiddleware: {
                publicPath: `${settings.STATIC_URL}dist/`,
            },
        },

        devServer: {
            disableHostCheck: true,
            hot: true,
            inline: true,
            progress: true,
            port: WEBPACK_DEBUG_PORT,
            proxy: {
                "**": {
                    target: `http://localhost:${DJANGO_DEBUG_PORT}`,
                },
            },
        },
        // Docs say to put this in.
        // But others say to leave it out. Currently, HMR only works if left out.
        // plugins: [
        //     new webpack.HotModuleReplacementPlugin(),
        // ],
    };
};
