import React from "react";
import {style} from "typestyle";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";
import {Fields, ManagementForm} from "reactivated/forms";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default (props: Types["DataBrowserProps"]) => (
    <Layout title="Data browser">
        <form>
            <h1 className={styles.header}>Composers</h1>
            <Fields form={props.composer_form} />
            <ManagementForm formSet={props.composer_form_set} />

            {props.composer_form_set.forms.map((formSetForm) => (
                <div key={formSetForm.prefix}>
                    <h2>{formSetForm.prefix}</h2>
                    <Fields form={formSetForm} />
                </div>
            ))}

            <h1 className={styles.header}>Operas</h1>
            <Fields form={props.opera_form} />
            <ManagementForm formSet={props.opera_form_set} />
            {props.opera_form_set.forms.map((formSetForm) => (
                <div key={formSetForm.prefix}>
                    <h2>{formSetForm.prefix}</h2>
                    <Fields form={formSetForm} />
                </div>
            ))}
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
