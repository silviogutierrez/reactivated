import React from "react";
import {style} from "typestyle";

import {Form} from "reactivated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Composers</h1>
        <ul>
        {props.composers.map((composer: any) =>
            <li key={composer.pk}>{composer.name}</li>
        )}
        </ul>
    </div>
)
