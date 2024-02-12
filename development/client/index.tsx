import React from "react";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

import {hydrateRoot} from "react-dom/client";

const {props, context} = getServerData();

const Template = getTemplate(context);

hydrateRoot(
    document.getElementById("root")!,
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
);
