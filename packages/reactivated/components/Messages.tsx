import React from "react";
import {Consumer} from "../context";

import {Alert} from "reactstrap";

const MESSAGE_LEVEL_CLASSES = {
    info: "info",
    success: "success",
    error: "danger",
    warning: "warning",
    debug: "secondary",
} as const;

export const Messages = (props: {}) => (
    <Consumer>
        {context => (
            <>
                {context.messages.map((message, index) =>
                    <Alert key={index} color={MESSAGE_LEVEL_CLASSES[message.level_tag]} fade={false}>
                        {message.message}
                    </Alert>
                )}
            </>
        )}
    </Consumer>
);
