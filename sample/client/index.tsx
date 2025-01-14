import React from "react";
import ReactDOM from "react-dom/client";

import {Provider, getTemplate, getServerData} from "@reactivated";

const {props, context} = getServerData();
const Template = await getTemplate({template_name: "HelloWorld"});

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <Provider value={context}>
            <Template {...props} />
        </Provider>
    </React.StrictMode>,
);
