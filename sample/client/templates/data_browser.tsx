import React from "react";
import {style} from "typestyle";

import {Form, FormSet} from "reactivated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: any) => (
    <div className={styles.layout}>
        <h1 className={styles.header}>Composers</h1>
        <Form form={props.composer_form}>
            <button type="submit">Submit</button>
        </Form>
        <FormSet formSet={props.composer_form_set}>
            <button type="submit">Submit</button>
        </FormSet>
        <h1 className={styles.header}>Operas</h1>
        <Form form={props.opera_form}>
            <button type="submit">Submit</button>
        </Form>
        <FormSet formSet={props.opera_form_set}>
            <button type="submit">Submit</button>
        </FormSet>
    </div>
)
