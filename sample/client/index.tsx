import React from "react";

import {hydrate} from "react-dom";
import {HelmetProvider} from "react-helmet-async";

import {Provider, getServerData, getTemplate} from "@client/generated";

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
