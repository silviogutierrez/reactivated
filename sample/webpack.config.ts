import MiniCssExtractPlugin from "mini-css-extract-plugin";
import {createConfig} from "reactivated/webpack";

const config = createConfig({
    DEBUG_PORT: parseInt(process.env["DEBUG_PORT"]!),
    MEDIA_URL: "/media/",
    STATIC_URL: "/static/",
    DEBUG: true,
});

// TODO: replace with function or something.
const options = {mode: "developoment"};

export default {
    ...config,
    plugins: [new MiniCssExtractPlugin({
        filename: "[name].css",
        chunkFilename: "[id].css",
    })],
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                exclude: /node_modules/,
                use: [
                    {loader: "babel-loader"},
                    {
                        loader: "linaria/loader",
                        options: {
                            sourceMap: options.mode !== "production",
                        },
                    },
                ],
            },
            {
                test: /\.css$/i,
                use: [
                    {loader: MiniCssExtractPlugin.loader},
                    {loader: "css-loader", options: {url: false}},
                ],
            },
        ],
    },
};
