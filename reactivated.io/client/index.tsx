import React from "react";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {hydrate} from "react-dom";
import {HelmetProvider} from "react-helmet-async";

const {props, context} = getServerData();

const Template = getTemplate(context);

hydrate(
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
    document.getElementById("root"),
);
