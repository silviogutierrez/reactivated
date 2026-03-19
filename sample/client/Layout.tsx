import React from "react";

interface Props {
    title: string;
    children?: React.ReactNode;
}

export const Layout = (props: Props) => {
    return (
        <html>
            <head>
                <meta charSet="utf-8" />
                <title>{props.title}</title>
                <meta
                    name="viewport"
                    content="width=device-width, initial-scale=1, shrink-to-fit=no"
                />
            </head>
            <body>
                <div className="mx-auto max-w-[1000px]">{props.children}</div>
            </body>
        </html>
    );
};
