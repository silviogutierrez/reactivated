import React from "react";

import {FieldHandler, Widget} from "@reactivated";

import {css} from "@linaria/core";
import {styled} from "@linaria/react";

import * as styles from "@client/styles";

export const Field = (props: {field: FieldHandler}) => {
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

export const button = styles.style({
    borderWidth: 2,
    borderStyle: "solid",
    borderColor: styles.colors.header,
    borderRadius: "5px",
    backgroundColor: styles.colors.header,
    padding: "10px 15px",
    font: "inherit",
    textTransform: "lowercase",
    fontWeight: 700,
    cursor: "pointer",
    textDecoration: "none",
    color: "white",
    display: "flex",
    alignItems: "center",
});

export const Button = styled.button`
    ${button}
`;

export const ButtonLink = styled.a`
    ${button}
`;
