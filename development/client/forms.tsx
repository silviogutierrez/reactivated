import React from "react";

import {FieldHandler, Widget, classNames, createRenderer} from "@reactivated";

import * as styles from "@client/styles.css";

export const Field = (props: {field: FieldHandler}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label className={styles.forms}>
            <div className={styles.sprinkles({fontWeight: 700})}>{field.label}</div>
            {renderedWidget}
            {field.error != null && (
                <div className={styles.sprinkles({color: "#cf0000"})}>
                    {field.error}
                </div>
            )}
        </label>
    );
};

export const Fields = createRenderer((field) => {
    return <Field field={field} />;
});

export const Fieldset = (props: {className?: string; children?: React.ReactNode}) => (
    <fieldset className={classNames(styles.Fieldset, props.className)}>
        {props.children}
    </fieldset>
);

export const Button = (props: {
    type: "submit" | "button";
    children?: React.ReactNode;
    onClick?: () => void;
}) => (
    <button onClick={props.onClick} type={props.type} className={styles.Button}>
        {props.children}
    </button>
);

export const ButtonLink = (props: {href: string; children?: React.ReactNode}) => (
    <a className={styles.ButtonLink} href={props.href}>
        {props.children}
    </a>
);
