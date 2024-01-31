import React from "react";
import ReactDOMServer from "react-dom/server";
import {App} from "./App";

export function render(templateName: string) {
    // @ts-ignore
    const templates = import.meta.glob("../client/templates/*.tsx", {eager: true});
    const Template = templates[`./templates/${templateName}.tsx`].default;

    const html = ReactDOMServer.renderToString(
        <React.StrictMode>
            <Template />
        </React.StrictMode>,
    );
    return {html};
}
