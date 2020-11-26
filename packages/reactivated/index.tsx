import React from "react";

export * from "./components/Form";
export {FormSet} from "./components/FormSet";
export * from "./components/SectionalForm";
export * from "./components/Widget";

import Context from "./context";

export const ServerData = () => {
    const props = (global as any).__REACTIVATED_PROPS ?? null;
    const context = React.useContext(Context);

    let serializedContext = "";
    let serializedProps = "";

    // Only execute on the server, where props won't be null.
    if (props != null) {
        // TODO: redux docs have this replacing, but since we're encoding, is it still really necessary?
        // See: https://redux.js.org/recipes/server-rendering#inject-initial-component-html-and-state
        serializedContext = Buffer.from(
            JSON.stringify(context).replace(/</g, "\\u003c"),
        ).toString("base64");
        serializedProps = Buffer.from(
            JSON.stringify(props).replace(/</g, "\\u003c"),
        ).toString("base64");
    }

    return (
        <>
            <meta
                name="reactivated-context"
                suppressHydrationWarning
                content={serializedContext}
            />
            <meta
                name="reactivated-props"
                suppressHydrationWarning
                content={serializedProps}
            />
        </>
    );
};
