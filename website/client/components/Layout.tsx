import React from "react";

import {Context} from "@reactivated";

import "@client/fonts.css";

interface Props {
    title: string | null;
    children: React.ReactNode;
}

export const Layout = (props: Props) => {
    const context = React.useContext(Context);

    return (
        <html>
            <head>
                <meta charSet="utf-8" />
                {props.title != null && <title>{props.title}</title>}
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link rel="preconnect" href="https://fonts.googleapis.com" />
                <link
                    rel="apple-touch-icon"
                    sizes="180x180"
                    href={`${context.STATIC_URL}apple-touch-icon.png`}
                />
                <link
                    rel="icon"
                    type="image/png"
                    sizes="32x32"
                    href={`${context.STATIC_URL}favicon-32x32.png`}
                />
                <link
                    rel="icon"
                    type="image/png"
                    sizes="16x16"
                    href={`${context.STATIC_URL}favicon-16x16.png`}
                />
            </head>
            <body>{props.children}</body>
        </html>
    );
};
