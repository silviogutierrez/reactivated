import React from "react";

const serJSON = (data: any): string => {
    return JSON.stringify(data).replace(/</g, "\\u003c");
};

export const PageShell = (
    props: React.PropsWithChildren<{
        vite: string;
        mode: "production" | "development";
        preloadContext: any;
        preloadProps: any;
        entryPoint: string;
    }>,
) => {
    const scriptNonce = props.preloadContext.request.csp_nonce
        ? `nonce="${props.preloadContext.request.csp_nonce}"`
        : "";
    const {STATIC_URL} = props.preloadContext;
    if (STATIC_URL == null) {
        console.error("Ensure your context processor includes STATIC_URL");
    }
    const headHTML = `
        ${props.vite}
        <script ${scriptNonce}>
            // These go first because scripts below need them.
            // WARNING: See the following for security issues around embedding JSON in HTML:
            // http://redux.js.org/recipes/ServerRendering.html#security-considerations
            window.__PRELOADED_PROPS__ = ${serJSON(props.preloadProps)};
            window.__PRELOADED_CONTEXT__ = ${serJSON(props.preloadContext)};
        </script>
        ${
            props.mode == "production"
                ? `<link rel="stylesheet" type="text/css" href="${STATIC_URL}dist/${props.entryPoint}.css">`
                : ""
        }
    `.trim();
    return (
        <html>
            <head dangerouslySetInnerHTML={{__html: headHTML}} />
            <body>
                <div id="root">{props.children}</div>
                {props.mode == "production" ? (
                    <script
                        type="module"
                        src={`${STATIC_URL}dist/${props.entryPoint}.js`}
                        defer
                        crossOrigin="anonymous"
                    ></script>
                ) : (
                    <script
                        type="module"
                        src={`${STATIC_URL}dist/client/${props.entryPoint}.tsx`}
                    ></script>
                )}
            </body>
        </html>
    );
};
