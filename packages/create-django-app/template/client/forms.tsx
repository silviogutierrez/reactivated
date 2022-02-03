import React from "react";

import {css} from "@linaria/core";

import {FieldHandler, Widget} from "reactivated/forms";

import {Types} from "@client/generated";

export const Field = (props: {field: FieldHandler<Types["globals"]["Widget"]>}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label
            className={css`
                display: block;
            `}
        >
            <div>{field.label}</div>
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
