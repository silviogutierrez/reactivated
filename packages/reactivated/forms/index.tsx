import React from "react";

export {FormLike, FormSetLike, ManagementForm} from "../components/Form";

import {Field} from "../components/Field";
import {FieldMap, FormLike} from "../components/Form";
import {SelectDateWidget, Widget, WidgetType} from "../components/Widget";
import Context from "../context";

export const CSRFToken = (props: {}) => {
    const context = React.useContext(Context);

    return (
        <input type="hidden" name="csrfmiddlewaretoken" value={context.csrf_token} />
    );
};

type FormValue<U extends WidgetType> = U extends SelectDateWidget
    ? {[subWidgetName: string]: U["subwidgets"][number]["value"]}
    : U["value"];

export type FormValues<U extends FieldMap> = {
    [K in keyof U]: FormValue<U[K]["widget"]>;
};

interface BaseFieldsProps<U extends FieldMap> {
    fieldInterceptor?: (form: FormLike<U>, fieldName: keyof U) => U[keyof U];
    changeInterceptor?: (
        name: keyof U,
        prevValues: FormValues<U>,
        nextValues: FormValues<U>,
    ) => FormValues<U>;
    form: FormLike<U>;
}

interface IncludeFieldsProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: Array<keyof U>;
    exclude?: never;
}

interface ExcludeFieldProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: never;
    exclude: Array<keyof U>;
}

type FieldsProps<U extends FieldMap> = IncludeFieldsProps<U> | ExcludeFieldProps<U>;

export const Fields = <U extends FieldMap>(props: FieldsProps<U>) => {
    const getField =
        props.fieldInterceptor ?? ((form, fieldName) => form.fields[fieldName]);

    const getIterator = () => {
        if (props.fields != null) {
            return props.fields;
        }

        if (props.exclude != null) {
            return props.form.iterator.filter(
                (field) => !props.exclude.includes(field),
            );
        }

        return props.form.iterator;
    };

    const iterator = getIterator();

    return (
        <>
            {iterator
                .map(
                    (fieldName) =>
                        [fieldName, getField(props.form, fieldName)] as const,
                )
                .map(([fieldName, field]) => {
                    const {widget} = field;
                    const error =
                        props.form.errors != null ? props.form.errors[fieldName] : null;

                    return (
                        <Field
                            key={field.widget.name}
                            field={field}
                            error={error ?? null}
                            passed_validation={
                                props.form.errors != null && error == null
                            }
                        />
                    );
                })}
        </>
    );
};
