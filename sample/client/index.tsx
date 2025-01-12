import React from "react";
import ReactDOM from "react-dom/client";

import {App} from "reactivated/dist/shell";

import {Provider, getTemplate, getServerData} from "@reactivated";
console.log("OK");

/*
const {props, context} = getServerData();
const Template = await getTemplate(context);
console.log(context.template_name);
*/

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <App />
    </React.StrictMode>,
    );

/*
import {Provider, getTemplate, getServerData} from "@reactivated";

const {props, context} = getServerData();
const Template = await getTemplate(context);
console.log("OK");

ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <PageShell
            vite=""
            mode="production"
            preloadContext={context}
            preloadProps={props}
            entryPoint="index"
        >
            <Provider value={context}>
                <Template {...props} />
            </Provider>
        </PageShell>
    </React.StrictMode>,
    );

*/