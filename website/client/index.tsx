import React from "react";
import {hydrate} from "react-dom";

import {Provider, getServerData, getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

const {props, context} = getServerData();

void getTemplate(context).then((Template) => {
    hydrate(
        <HelmetProvider>
            <Provider value={context}>
                <Template {...props} />
            </Provider>
        </HelmetProvider>,
        document.getElementById("root"),
    );
});
