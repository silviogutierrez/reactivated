import React from "react";

import {FieldHandler, Widget} from "@reactivated";

import * as styles from "@client/styles.css";

export const Field = (props: {field: FieldHandler}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label
            style={{
                display: "block",
            }}
        >
            <div
                style={{
                    fontWeight: 700,
                }}
            >
                {field.label}
            </div>
            {renderedWidget}
            {field.error != null && (
                <div
                    style={{
                        color: "#cf0000",
                    }}
                >
                    {field.error}
                </div>
            )}
        </label>
    );
};

export const Button = (props: JSX.IntrinsicElements["button"]) => (
    <button {...props} className={styles.Button} />
);

export const ButtonLink = (props: JSX.IntrinsicElements["a"]) => (
    <a {...props} className={styles.Button} />
);
