import React from "react";
import {hydrateRoot} from "react-dom/client";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

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
