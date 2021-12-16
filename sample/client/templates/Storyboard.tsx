import React from "react";

import {CSRFToken, Types} from "@client/generated";
import {Layout} from "@client/Layout";

import {Fields, useForm, Widget} from "reactivated/forms/genesis";

const SPACING = 2;

export default (props: Types["StoryboardProps"]) => {
    const handler = useForm({form: props.form});
    // handler.values.date_time_field;
    // handler.values.date_field;

    return (
        <Layout title="Storyboard">
            <h1>Storyboard</h1>
            <form action="" method="POST">
                <CSRFToken />
                <Fields form={handler}>
                    {(field) => (
                        <>
                            <h2>{field.name}</h2>
                            <p>
                                <Widget field={field} />
                            </p>
                        </>
                    )}
                </Fields>
                <button type="submit">Submit</button>
            </form>
            <h1>Values</h1>
            <pre>{JSON.stringify(handler.values, null, SPACING)}</pre>
            <h1>Form</h1>
            <pre>{JSON.stringify(props.form, null, SPACING)}</pre>
        </Layout>
    );
};
