import React from "react";
import {hydrate} from "react-dom";

import {getServerData, Provider} from "@client/generated";

const {props, context} = getServerData();

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + context.template_name).default;

hydrate(
    <Provider value={context}>
        <Template {...props} />
    </Provider>,
    document.getElementById("root"),
);
