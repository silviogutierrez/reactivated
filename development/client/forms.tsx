import React from "react";

import {css} from "@linaria/core";
import {styled} from "@linaria/react";

import {FieldHandler, Widget} from "reactivated/forms";

import {Types} from "@client/generated";
import * as styles from "@client/styles";

export {useFormSet, ManagementForm} from "reactivated/forms";

export const Field = (props: {field: FieldHandler<Types["globals"]["Widget"]>}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label
            className={css`
                ${styles.verticallySpaced(5)}
                display: block;
            `}
        >
            <div
                className={css`
                    font-weight: 700;
                `}
            >
                {field.label}
            </div>
            {renderedWidget}
            {field.error != null && (
                <div
                    className={css`
                        color: #cf0000;
                    `}
                >
                    {field.error}
                </div>
            )}
        </label>
    );
};

export const Fieldset = styled.fieldset`
    border: 1px solid #bbb;
    border-radius: 5px;
    padding: 20px;
`;

export const Button = styled.button`
    border: 1px solid #bbb;
    border-radius: 5px;
    padding: 10px 15px;
    font: inherit;
    text-transform: lowercase;
    font-weight: 700;
    background-color: white;
    color: #444;
    cursor: pointer;
`;

export const ButtonLink = styled.a`
    display: inline-block;
    border: 1px solid #bbb;
    border-radius: 5px;
    padding: 10px 15px;
    font: inherit;
    text-transform: lowercase;
    font-weight: 700;
    background-color: white;
    color: #444;
    cursor: pointer;
    text-decoration: none;
`;
