import React from "react";

interface Props {
    children?: React.ReactNode;
}

export const Layout = (props: Props) => <div>{props.children}</div>;
