import React from "react";

import {css} from "@linaria/core";

import {FieldHandler, ManagementForm, Widget, useFormSet} from "reactivated/forms";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Iterator, Types} from "@client/generated";

export const Field = (props: {field: FieldHandler<Types["globals"]["Widget"]>}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label>
            {field.label}
            {renderedWidget}
            {field.error != null && (
                <div
                    className={css`
                        color: red;
                    `}
                >
                    {field.error}
                </div>
            )}
        </label>
    );
};

export default (props: Types["CreatePollProps"]) => {
    const formSet = useFormSet({formSet: props.choice_form_set});

    return (
        <Layout title="Create question">
            <h1>Create poll</h1>
            <form method="POST" action="">
                <CSRFToken />
                <Iterator form={props.form}>
                    {(field) => <Field field={field} />}
                </Iterator>
                <ManagementForm formSet={formSet.schema} />

                {formSet.handlers.map((handler) => (
                    <div key={handler.form.prefix}>
                        <Iterator form={handler}>
                            {(field) => <Field field={field} />}
                        </Iterator>
                    </div>
                ))}
                <button type="submit">Submit</button>
            </form>
        </Layout>
    );
};
