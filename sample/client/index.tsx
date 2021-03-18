import React from "react";
import {hydrate} from "react-dom";
import {HelmetProvider} from "react-helmet-async";

import {getServerData} from "reactivated";
import {Provider} from "reactivated/context";

const {props, context} = getServerData<Parameters<typeof Provider>[0]["value"]>();

if ((module as any).hot) {
    (module as any).hot.accept();
}

// tslint:disable-next-line
const Template = require("client/templates/" + context.template_name).default;

hydrate(
    <HelmetProvider>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </HelmetProvider>,
    document.getElementById("root"),
);
