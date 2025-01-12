import React from "react";

import {Layout} from "@client/Layout";
import {templates} from "@reactivated";
import * as styles from "@client/styles.css";

const Paragraph = (props: {children?: React.ReactNode}) => (
    <p className={styles.Paragraph}>{props.children}</p>
);

export const Template = (props: templates.HelloWorld) => {
    const [showStyle, setShowStyle] = React.useState(false);
    const id = React.useId();

    return (
        <div>
            <h1>Hello World! {id} 3</h1>
            <style type="text/css">{`
        @font-face {
           font-family: Montserrat;
           font-style: "normal";
           font-weight: 500;
           src: url('/static/fonts/montserrat-v14-latin-500.woff2') format('woff2');
        }

            
            
            body { background-color: red; }`}</style>
        </div>
    );
};
