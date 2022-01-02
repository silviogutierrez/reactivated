import React from "react";
import {Helmet} from "react-helmet-async";

import * as styles from "@client/components/Layout.css.ts"

interface Props {
    title: string;
    children?: React.ReactNode;
}

export const Layout = (props: Props) => {
    return (
        <>
            <Helmet>
                <meta charSet="utf-8" />
                <title>{props.title}</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, shrink-to-fit=no"
                />

                <script defer src="/bundles/client.js" />
                <link
                    href={`/bundles/client.css`}
                    rel="stylesheet"
                />
            </Helmet>
            <div className={styles.layout}>{props.children}</div>
        </>
    );
};
