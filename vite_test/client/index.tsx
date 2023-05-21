import React from "react";
import {createRoot} from "react-dom/client";
import {HelmetProvider} from "react-helmet-async";
// import "./index.css"
// import "./index.css"

import otherStyles from "./index.css?inline";
console.log(otherStyles);

const root = createRoot(document.getElementById("root")!);

import HomePage from "./templates/HomePage";

root.render(
    <HelmetProvider>
        <style>{otherStyles}</style>
        <HomePage />
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
