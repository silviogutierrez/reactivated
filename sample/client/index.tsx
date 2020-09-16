import React from "react";
import {hydrate} from "react-dom";
import {setStylesTarget} from "typestyle";

import {Provider} from "reactivated/context";

const props = (window as any).__PRELOADED_PROPS__;
const context = (window as any).__PRELOADED_CONTEXT__;

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + context.template_name).default;

setStylesTarget(document.getElementById("styles-target")!);

hydrate(
    <Provider value={context}>
        <Template {...props} />
    </Provider>,
    document.getElementById("root"),
);
