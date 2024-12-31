import React from "react";
import ReactDOM from "react-dom/client";

import {Provider, getTemplate, getServerData} from "@reactivated";

const {props, context} = getServerData();
const Template = await getTemplate(context);

ReactDOM.hydrateRoot(
    document.getElementById("root") as HTMLElement,
    <React.StrictMode>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </React.StrictMode>,
);
