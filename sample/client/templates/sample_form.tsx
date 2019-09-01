import React from "react";
import {style} from "typestyle";

import {Form} from "reactivated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Sample form!</h1>
        <Form form={props.form}>
            <button type="submit">Submit</button>
        </Form>
    </div>
);
