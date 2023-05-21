import React from "react";
import {createRoot} from "react-dom/client";
import {HelmetProvider} from "react-helmet-async";
import "./index.css";
// import {getServerData} from "@reactivated"

const root = createRoot(document.getElementById("root")!);

const props: any = (window as any).__PRELOADED_PROPS__;
const context: any = (window as any).__PRELOADED_CONTEXT__;
console.log(context.template_name);

// @ts-ignore
const templates = import.meta.glob("@client/templates/*.tsx", {eager: true});
const Template = templates[`/client/templates/${context.template_name}.tsx`].default;

root.render(
    <HelmetProvider>
        <Template {...props} />
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
