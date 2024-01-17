import React from "react";

import {Options} from "reactivated/dist/conf";

export default {
    build: {
        client: (options) => {},
        renderer: () => {},
    },
    render: (content) => <div>I AM HERE {content}</div>,
} satisfies Options;
