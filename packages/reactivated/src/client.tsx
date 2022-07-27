import React from "react";
import {hydrate} from "react-dom";

const props = (window as any).__PRELOADED_STATE__;

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + props.template_name + ".tsx").default;

export const bootstrap = () => {
    hydrate(<Template {...props} />, document.getElementById("root"));
};
