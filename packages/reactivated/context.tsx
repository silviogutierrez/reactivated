import React from "react";

import * as models from "./models";

const Context = React.createContext({
    request: {
        path: "",
        url: "",
    },
    template_name: "",
    csrf_token: "",
    messages: [] as models.Message[],
});

export const {Consumer, Provider} = Context;

export default Context;
