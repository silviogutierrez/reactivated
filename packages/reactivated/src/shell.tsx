import React from "react";

const serJSON = (data: any): string => {
    return JSON.stringify(data).replace(/</g, "\\u003c");
};

export function App(props: {children?: React.ReactNode}) {
    return (
        <html>
            <body>
                Hello 5
                <button
                    onClick={() => {
                        console.log("Done");
                    }}
                >
                    Done
                </button>
                {props.children}
            </body>
        </html>
    );
}

export const PageShell = (
    props: React.PropsWithChildren<{
        vite: string;
        mode: "production" | "development";
        preloadContext: any;
        preloadProps: any;
        entryPoint: string;
    }>,
) => {
    /*
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
    */
    return (
        <html>
            <body>Hello</body>
        </html>
    );
};
