import React from "react";
import {HelmetProvider} from "react-helmet-async";

interface Props {
    title: string;
    children?: React.ReactNode;
}

export const Layout = (props: Props) => {
    return (
        <>
            <HelmetProvider>
                <meta charSet="utf-8" />
                <title>{props.title}</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, shrink-to-fit=no"
                />

                <script defer src="/bundles/client.js" />
            </HelmetProvider>
            <div>{props.children}</div>
        </>
    );
};
