import React from "react";
import {style} from "typestyle";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default () => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Hello world!</h1>
        <p>I am a paragraph</p>
        <p>I am another paragraph</p>
    </div>
);
