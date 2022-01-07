import React from "react";
import {hydrate} from "react-dom";

import templates, {filenames} from "./templates/**/*";
import {getServerData} from "@client/generated";

import {HelmetProvider} from "react-helmet-async";

const REACTIVATED_CLIENT_ROOT = ".";

const {props, context} = getServerData();

const templatePath = `${REACTIVATED_CLIENT_ROOT}/templates/${context.template_name}.tsx`;
const Template = templates.find(
    (t, index) => filenames[index] === templatePath,
).default;

hydrate(
    <HelmetProvider>
        <Template {...props} />
    </HelmetProvider>,
    document.getElementById("root"),
);
