import React from "react";
import Helmet from "react-helmet";

import Context from "reactivated/context";
import {style} from "typestyle";

interface Props {
    title: string;
    children?: React.ReactNode;
}

const styles = {
    layout: style({maxWidth: 800, margin: "0 auto"}),
} as const;

export const Layout = (props: Props) => {
    const context = React.useContext(Context);

    return (
        <>
            <Helmet key={context.request.path}>
                <meta charSet="utf-8" />
                <title>{props.title}</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, shrink-to-fit=no"
                />

                <script defer src="/media/dist/bundle.js" />
            </Helmet>
            <div className={styles.layout}>{props.children}</div>
        </>
    );
};
