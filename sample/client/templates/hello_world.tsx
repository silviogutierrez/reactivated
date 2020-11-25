import React from "react";
import Context from "reactivated/context";
import {style} from "typestyle";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

const Foo = () => {
    const context = React.useContext(Context);
    const props = (global as any).__REACTIVATED_PROPS ?? null;
    const serializedContext = JSON.stringify(context).replace(/</g, "\\u003c");
    const serializedProps = JSON.stringify(props).replace(/</g, "\\u003c");

    return (
        <>
            <meta name="reactivated-context" content={serializedContext} />
            <meta
                name="reactivated-props"
                suppressHydrationWarning
                content={serializedProps}
            />
        </>
    );
};

export default () => (
    <>
        <head>
            <Foo />
            <title>Hello world</title>
            <meta
                name="viewport"
                content="width=device-width, initial-scale=1, shrink-to-fit=no"
            />
            <script defer src="/media/dist/bundle.js" />
        </head>
        <body>
            <div className={styles.layout}>
                <h1 className={styles.header}>Hello world!</h1>
                <p>I am a paragraph</p>
                <p>I am another paragraph</p>
            </div>
        </body>
    </>
);
