import React from "react";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

import {createRoot} from "react-dom/client";

const {props, context} = getServerData();

const Template = getTemplate(context);

const root = createRoot(document.getElementById("root")!);
root.render(
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
);

if (process.env.ESBUILD_SERVE_PORT) {
    (function connectLiveReload() {
        const url = `//${window.location.hostname}:${process.env.ESBUILD_SERVE_PORT}/esbuild`;
        const bundler = new EventSource(url);
        bundler.addEventListener("change", () => {
            location.reload();
        });
        bundler.addEventListener("error", () => {
            bundler.close();
            setTimeout(connectLiveReload, 500);
        });
    })();
}
