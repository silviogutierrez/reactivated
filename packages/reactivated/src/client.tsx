import {hydrateRoot} from "react-dom/client";
import React from "react";

const props = (window as any).__PRELOADED_STATE__;

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + props.template_name + ".tsx").default;

export const bootstrap = () => {
    const root = document.getElementById("root");
    if (!root) {
        console.error("div#root is missing!");
        return;
    }
    hydrateRoot(root, <Template {...props} />);
};
