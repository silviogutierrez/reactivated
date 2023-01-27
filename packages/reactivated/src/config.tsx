import React from "react";
import {BuildOptions} from "esbuild";

export type Config = Readonly<{
    clientBuildConfig: (options: BuildOptions) => BuildOptions;
    rendererBuildConfig: (options: BuildOptions) => BuildOptions;
    renderPage: (template: React.ReactNode) => React.ReactNode;
}>;

const ident = <T,>(x: T) => x;
const defaults: Config = {
    clientBuildConfig: ident,
    rendererBuildConfig: ident,
    renderPage: ident,
};

/**
 * Function exists mainly just for type checking
 */
export const config = (c: Partial<Config>): Partial<Config> => {
    return c;
};

/**
 * Load the project custom configuration
 */
export const loadConfig = (): Config => {
    let overrides: Partial<Config> = {};
    try {
        overrides = require(`${process.cwd()}/client/reactivated.conf`).default;
    } catch (e) {
        console.debug(`Could not load @client/reactivated.conf: ${e}`);
    }
    return {
        ...defaults,
        ...overrides,
    };
};
