import React from "react";
import {style} from "typestyle";

import {Form, FormSet} from "reactivated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1>Hello</h1>
    </div>
)
