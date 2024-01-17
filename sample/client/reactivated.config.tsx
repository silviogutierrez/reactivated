import React from "react";

import {Options} from "reactivated/dist/conf";

export default {
    build: {
        client: (options) => {},
        renderer: () => {},
    },
    render: async (content) => {
        const {ThemeContext} = await import("@client/context");

        return <ThemeContext.Provider value="light">{content}</ThemeContext.Provider>;
    },
} satisfies Options;
