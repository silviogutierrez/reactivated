import React from "react";

import {Options} from "@reactivated";

export default {
    build: {
        client: (options) => options,
        renderer: (options) => options,
    },
    render: async (content) => {
        return <>{content}</>;
    },
} satisfies Options;
