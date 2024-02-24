import React from "react";

import {CSRFToken, Form, FormSet, templates} from "@reactivated";

import {Layout} from "@client/components/Layout";

export const Template = (props: templates.FormPlayground) => (
    <Layout title="Forms">
        <h1>Forms</h1>
        <form method="POST" action="">
            <CSRFToken />
            <table>
                <tbody>
                    <Form form={props.form} as="table" />
                </tbody>
            </table>
            <button type="submit">Submit</button>
        </form>
        <form method="POST" action="">
            <CSRFToken />
            <Form form={props.form_as_p} as="p" />
            <button type="submit">Submit</button>
        </form>
        <form method="POST" action="">
            <CSRFToken />
            <table>
                <tbody>
                    <FormSet formSet={props.form_set} as="table" />
                </tbody>
            </table>
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
