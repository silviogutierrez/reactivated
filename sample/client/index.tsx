import React from "react";
import ReactDOM from "react-dom/client";

import {App} from "reactivated/dist/shell";

import {Provider, getTemplate, getServerData} from "@reactivated";

const {props, context} = getServerData();
const Template = await getTemplate({template_name: "HelloWorld"});
console.log(context);


ReactDOM.hydrateRoot(
    document,
    <React.StrictMode>
        <Provider value={context}>
            <Template />
        </Provider>
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