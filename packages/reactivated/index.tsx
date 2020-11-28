import React from "react";

export * from "./components/Form";
export {FormSet} from "./components/FormSet";
export * from "./components/SectionalForm";
export * from "./components/Widget";

import Context from "./context";

export const getServerData = <T extends {}>() => {
    const props = (window as any).__PRELOADED_PROPS__;
    const context: T = (window as any).__PRELOADED_CONTEXT__;

    return {props, context};
};
