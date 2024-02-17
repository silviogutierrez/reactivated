import React from "react";
import {Renderer} from "@reactivated";

export default ((content) => {
    return Promise.resolve(<>{content}</>);
}) satisfies Renderer;
