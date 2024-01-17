import { BuildOptions } from "esbuild";

export type Options = {
    build?: {
        client?: (options: BuildOptions) => void;
        renderer?: (options: BuildOptions) => void;
    }
    render?: (content: JSX.Element) => JSX.Element;
}

export const configure = (options: Options) => options;