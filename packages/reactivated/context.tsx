// Note: changing the file requires restarting the development server
import React from "react";
import {createTypeStyle, TypeStyle} from "typestyle";

import * as models from "./models";

const Context = React.createContext({
    request: {
        path: "",
        url: "",
    },
    template_name: "",
    csrf_token: "",
    messages: [] as models.Message[],
    typestyle: createTypeStyle(),
});

export const {Consumer, Provider} = Context;

export default Context;
