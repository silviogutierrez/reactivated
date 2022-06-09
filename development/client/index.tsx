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
