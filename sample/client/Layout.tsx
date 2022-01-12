import React from "react";
import {HelmetProvider} from "react-helmet-async";

interface Props {
    title: string;
    children?: React.ReactNode;
}

const styles = {
    layout: {margin: "0 auto", maxWidth: 1000},
} as const;

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

                <script defer src="/static/dist/index.js" />
            </HelmetProvider>
            <div style={styles.layout}>{props.children}</div>
        </>
    );
};
