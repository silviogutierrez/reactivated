import React from "react";

import {Provider, getServerData, getTemplate} from "@reactivated";

import {createRoot} from "react-dom/client";

const {props, context} = getServerData();
const Template = await getTemplate(context);

const root = createRoot(document.getElementById("root")!);
root.render(
    <Provider value={context}>
        <Template {...props} />
    </Provider>,
);
