import React from "react";
import {style} from "typestyle";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";
import {Form, FormSet} from "reactivated";
import {Fields} from "reactivated/forms";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: Types["DataBrowserProps"]) => (
    <Layout title="Data browser">
        <h1 className={styles.header}>Composers</h1>
        <form>
            <Fields form={props.composer_form} fields={["name"]} />
        </form>
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
    </Layout>
);
