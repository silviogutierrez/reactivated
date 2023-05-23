import React from "react";

import {createRoot} from "react-dom/client";
import {Provider, getServerData} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

import "@client/index.css";

const root = createRoot(document.getElementById("root")!);
const {props, context} = getServerData();

// @ts-ignore
const templates = import.meta.glob("@client/templates/*.tsx", {eager: true});
const Template = templates[`/client/templates/${context.template_name}.tsx`].default;

root.render(
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
);

/*
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
*/
