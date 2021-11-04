import React, { useDebugValue } from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types} from "@client/generated";
// import {useForm, FormLike, FormHandler, FieldMap} from "reactivated/forms";
import {useForm, Form} from "@client/forms"

export default (props: Types["CreateOperaProps"]) => {
    const form = useForm({form: props.form});

    return (
        <Layout title="Create opera">
            <form method="POST" action="">
                <CSRFToken />
                <div style={{display: "flex"}}>
                    <Form form={props.form} />
                    <Form form={props.pre_filled} />
                    <Form form={props.posted} />
                </div>
                <input type="submit" value="Submit" />
            </form>
        </Layout>
    );
};
