import React from "react";
import ReactDOM from "react-dom/client";
import {createRoot} from "react-dom/client";

import {Provider, viteGetTemplate, getServerData} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

const {props, context} = getServerData();

const Template = viteGetTemplate(context);

ReactDOM.hydrateRoot(
    document.getElementById("root") as HTMLElement,
    <React.StrictMode>
        <HelmetProvider>
            <Provider value={context}>
                <Template {...props} />
            </Provider>
        </HelmetProvider>
    </React.StrictMode>,
);
