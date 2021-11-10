import React, {useDebugValue} from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types} from "@client/generated";
import {useForm, Widget} from "reactivated/forms/genesis";
// import {Form} from "@client/forms";
// import {useForm, FormLike, FormHandler, FieldMap} from "reactivated/forms";


export default (props: Types["CreateOperaProps"]) => {
    const form = useForm({form: props.form});
    const fields = form.iterate((field) => {
        if (field.tag === "django.forms.widgets.Select") {
            field.value
        }
        else if (field.tag === "django.forms.widgets.CheckboxInput") {
            field.value
        }
        return <div>Ok</div>
    }
    );

    return (
        <Layout title="Create opera">
            <form method="POST" action="">
                <CSRFToken />
                <div style={{display: "flex"}}>
                    {/*
                    <Form form={props.form} />
                    <Form form={props.pre_filled} />
                    <Form form={props.posted} />
                    */}
                </div>
                <input type="submit" value="Submit" />
            </form>
        </Layout>
    );
};
