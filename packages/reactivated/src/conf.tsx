import {BuildOptions} from "esbuild";

export type Options = {
    build?: {
        client?: (options: BuildOptions) => void;
        renderer?: (options: BuildOptions) => void;
    };
    render?: (content: JSX.Element) => JSX.Element;
};

export const configure = (options: Options) => options;

export default (customConfigurationImport: {default?: Options} | null) => {
    const customConfiguration = customConfigurationImport?.default ?? {};

    return {
        build: {
            client: customConfiguration.build?.client ?? ((options) => {}),
            renderer: customConfiguration.build?.renderer ?? ((options) => {}),
        },
        render: customConfiguration.render ?? ((content) => content),
    } satisfies Options;
};
