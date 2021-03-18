import React from "react";
import {css} from "@linaria/core";

const styles = {
    layout: css`
        ${{maxWidth: 600, margin: "0 auto"}}
    `,

    header: css`
        ${{color: "blue"}}
    `,
} as const;

export default () => (
    <div className={styles.layout}>
        <link href={`/static/dist/main.css`} rel="stylesheet" />
        <h1 className={styles.header}>Hello world!</h1>
        <p>I am a paragraph</p>
        <p>I am another paragraph</p>
    </div>
);
