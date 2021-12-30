import React from "react";
import {hydrate} from "react-dom";

import templates, {filenames} from './templates/**/*';

import {HelmetProvider} from "react-helmet-async";

const REACTIVATED_CLIENT_ROOT = ".";

const getServerData = () => {
    return {props: {}, context: {
        template_name: document.location.href.includes("Page") ? "Page.tsx" : "Login.tsx",
    }};
}

const {props, context} = getServerData();

const templatePath = `${REACTIVATED_CLIENT_ROOT}/templates/${context.template_name}`;
const Template = templates.find((t, index) => filenames[index] === templatePath).default;

hydrate(
    <HelmetProvider>
            <Template {...props} />
    </HelmetProvider>,
    document.getElementById("root"),
);
