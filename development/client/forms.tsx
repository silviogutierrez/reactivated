import React from "react";

import {FieldHandler, Widget, classNames, createRenderer} from "@reactivated";

export const Field = (props: {field: FieldHandler}) => {
    const {field} = props;
    const renderedWidget = <Widget field={field} />;

    if (field.tag == "django.forms.widgets.HiddenInput") {
        return renderedWidget;
    }

    return (
        <label className="forms">
            <div className="font-bold">{field.label}</div>
            {renderedWidget}
            {field.error != null && (
                <div className="text-[#cf0000]">{field.error}</div>
            )}
        </label>
    );
};

export const Fields = createRenderer((field) => {
    return <Field field={field} />;
});

export const Fieldset = (props: {className?: string; children?: React.ReactNode}) => (
    <fieldset className={classNames("Fieldset", props.className)}>
        {props.children}
    </fieldset>
);

export const Button = (props: {
    type: "submit" | "button";
    children?: React.ReactNode;
    onClick?: () => void;
}) => (
    <button onClick={props.onClick} type={props.type} className="Button">
        {props.children}
    </button>
);

export const ButtonLink = (props: {href: string; children?: React.ReactNode}) => (
    <a className="ButtonLink" href={props.href}>
        {props.children}
    </a>
);
