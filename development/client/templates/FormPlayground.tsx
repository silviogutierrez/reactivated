import React from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Form, Types} from "@client/generated";

export default (props: Types["FormPlaygroundProps"]) => (
    <Layout title="Forms">
        <h1>Forms</h1>
        <form method="POST" action="">
            <CSRFToken />
            <table>
                <tbody>
                    <Form form={props.form} as="table">
                        <button type="submit">Submit</button>
                    </Form>
                </tbody>
            </table>
        </form>
        <form method="POST" action="">
            <CSRFToken />
            <Form form={props.form_as_p} as="p">
                <button type="submit">Submit</button>
            </Form>
        </form>
    </Layout>
);
