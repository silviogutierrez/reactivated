import React from "react";
import {css} from "@linaria/core";

const styles = {
    layout: css`${{maxWidth: 600, margin: "0 auto"}}`,

    header: css`${{color: "blue"}}`,
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Composers</h1>
        <ul>
            {props.composers.map((composer: any) => (
                <li key={composer.pk}>{composer.name}</li>
            ))}
        </ul>
    </div>
);
