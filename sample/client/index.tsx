import React from "react";
import {hydrate} from "react-dom";

import {Provider} from "reactivated/context";

const props = JSON.parse((document.getElementsByName("reactivated-props")[0] as HTMLMetaElement).content);
const context = JSON.parse((document.getElementsByName("reactivated-context")[0] as HTMLMetaElement).content);

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + context.template_name).default;

hydrate(
    <Provider value={context}>
        <Template {...props} />
    </Provider>,
    document.documentElement
);
