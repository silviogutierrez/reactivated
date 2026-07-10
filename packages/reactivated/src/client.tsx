import React from "react";
import {hydrateRoot} from "react-dom/client";

export interface RenderInfo<TContext = unknown> {
    /** True during server-side rendering, false during browser hydration. */
    ssr: boolean;
    context: TContext;
    props: unknown;
}

export interface ReactivateConfig<TContext = unknown> {
    /**
     * Browser-only setup, awaited before hydration. Never runs during SSR,
     * so it may touch window, cordova, analytics — anything. Imports of
     * browser-dirty libraries belong in here as dynamic imports; the entry
     * module itself is evaluated during SSR and its module scope must stay
     * node-safe.
     */
    init?: (server: {context: TContext; props: unknown}) => void | Promise<void>;
    /**
     * Wraps the rendered template with app providers. Runs on both sides —
     * keep it pure so server and client markup agree. The ssr flag exists
     * for per-side resources (e.g. a fresh store per SSR request vs the
     * browser singleton).
     */
    render?: (
        content: React.JSX.Element,
        info: RenderInfo<TContext>,
    ) => React.JSX.Element | Promise<React.JSX.Element>;
    /**
     * Browser-only. Defining this hook means mounting is yours: the
     * framework resolves the template and applies render, then hands you
     * the prepared element instead of hydrating. Call
     * hydrateRoot(document, content) for the default behavior, or mount
     * something else entirely (e.g. an SPA root via createRoot). SSR is
     * unaffected; render still runs server-side.
     */
    mount?: (server: {
        context: TContext;
        props: unknown;
        content: React.JSX.Element;
    }) => void | Promise<void>;
}

declare global {
    // eslint-disable-next-line no-var
    var __REACTIVATED_CONFIG__: ReactivateConfig<any> | undefined;
}

/** The registered config; read by the SSR renderer after entry evaluation. */
export const getReactivateConfig = (): ReactivateConfig<any> =>
    globalThis.__REACTIVATED_CONFIG__ ?? {};

/**
 * The one entry point. Call it from client/index.tsx (or let the virtual
 * default entry call it bare). During SSR the entry module is evaluated for
 * its side effect: reactivate() registers the config and returns. In the
 * browser it parses the preloaded server data, awaits init, resolves the
 * template, wraps it with render, and hydrates.
 */
export const reactivate = <TContext,>(
    config: ReactivateConfig<TContext> = {},
): void => {
    globalThis.__REACTIVATED_CONFIG__ = config as ReactivateConfig<any>;

    if (typeof window === "undefined") {
        return;
    }

    void (async () => {
        const props = (window as any).__PRELOADED_PROPS__;
        const context = (window as any).__PRELOADED_CONTEXT__ as TContext;

        await config.init?.({context, props});

        const {getTemplate} = await import("virtual:reactivated/templates");
        // @ts-ignore
        const {Provider} = await import("@reactivated");

        const Template = await getTemplate(context);

        const content = (
            <React.StrictMode>
                <Provider value={context}>
                    <Template {...(props as object)} />
                </Provider>
            </React.StrictMode>
        );

        const wrapped = await (config.render ?? ((c: React.JSX.Element) => c))(
            content,
            {ssr: false, context, props},
        );

        if (config.mount != null) {
            await config.mount({context, props, content: wrapped});
            return;
        }

        hydrateRoot(document, wrapped);
    })();
};

/**
 * Hydrate an SSR'd template fragment inside a page the framework does not
 * own — the Django admin being the canonical case. The base template marks
 * the fragment root with data-reactivated-root; absent that marker this is
 * a no-op, so calling it unconditionally from an admin entry is safe.
 */
export const reactivateAdmin = (): void => {
    if (typeof window === "undefined") {
        return;
    }
    const fragmentRoot = document.querySelector("[data-reactivated-root]");
    if (fragmentRoot == null) {
        return;
    }
    void (async () => {
        const props = (window as any).__PRELOADED_PROPS__;
        const context = (window as any).__PRELOADED_CONTEXT__;

        const {getTemplate} = await import("virtual:reactivated/templates");
        // @ts-ignore
        const {Provider} = await import("@reactivated");

        const Template = await getTemplate(context);
        hydrateRoot(
            fragmentRoot,
            <React.StrictMode>
                <Provider value={context}>
                    <Template {...(props as object)} />
                </Provider>
            </React.StrictMode>,
        );
    })();
};
