import type {ClientConfig, RendererConfig} from "./build.client.mjs";
import type {InlineConfig} from "vite";

export type Options = {
    build?: {
        client?: (options: ClientConfig) => InlineConfig;
        renderer?: (options: RendererConfig) => InlineConfig;
    };
    render?: (content: JSX.Element) => Promise<JSX.Element>;
};

export type Foo = (first: string) => void;

export default ((first) => {}) satisfies Foo;
