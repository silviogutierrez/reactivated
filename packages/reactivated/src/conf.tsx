import type {ClientConfig, RendererConfig} from "./build.client.mjs";
import type {InlineConfig} from "vite";

export type Options = {
    build?: {
        client?: (options: ClientConfig) => InlineConfig;
        renderer?: (options: RendererConfig) => InlineConfig;
    };
    render?: (content: JSX.Element) => Promise<JSX.Element>;
};

export const define = () => {
    const production = process.env.NODE_ENV === "production";
    const env = {
        NODE_ENV: production ? "production" : "development",
        BUILD_VERSION: process.env.BUILD_VERSION,
        TAG_VERSION: process.env.TAG_VERSION,
        RELEASE_VERSION: process.env.RELEASE_VERSION,
    };

    return {
        // You need both. The one from the stringified JSON is not picked
        // up during the build process.
        "process.env.NODE_ENV": production ? '"production"' : '"development"',
        "process.env": JSON.stringify(env),
    };
};
