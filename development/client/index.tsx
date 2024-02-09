import React from "react";

import {Provider, getServerData, viteGetTemplate as getTemplate} from "@reactivated";
import {HelmetProvider} from "react-helmet-async";

import {createRoot} from "react-dom/client";

const {props, context} = getServerData();

void getTemplate(context).then((Template) => {
    const root = createRoot(document.getElementById("root")!);
    root.render(
        <HelmetProvider>
            <Provider value={context}>
                <Template {...props} />
            </Provider>
        </HelmetProvider>,
    );
});
