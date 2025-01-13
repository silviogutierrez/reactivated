import React from "react";
import ReactDOM from "react-dom/client";

import {Provider, getServerData, getTemplate} from "@reactivated";

import {createRoot} from "react-dom/client";

const {props, context} = getServerData();
const Template = await getTemplate(context);

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </React.StrictMode>,
);
