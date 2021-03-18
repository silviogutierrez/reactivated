import React from "react";
import {css} from "@linaria/core";

import {Form} from "reactivated";

const styles = {
    layout: css`${{maxWidth: 600, margin: "0 auto"}}`,

    header: css`${{color: "blue"}}`,
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Create opera</h1>
        <Form form={props.form}>
            <button type="submit">Submit</button>
        </Form>
    </div>
);
