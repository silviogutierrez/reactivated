import React from "react";

import {Types} from "../generated";
import * as widgets from "./widgets";

export interface OptgroupMember {
  name: string;
  value: string | number | boolean | null;
  label: string;
  selected: boolean;
}

export type Optgroup = [null, [OptgroupMember], number];

export type WidgetLike = {name: string, tag: string, value_from_datadict: unknown, subwidgets?: WidgetLike[], value: unknown};

import {Formatters} from "tslint";

// Move to utilities?
type DiscriminateUnion<T, K extends keyof T, V extends T[K]> = T extends Record<K, V>
    ? T
    : never;

type Simplify<T> = {[KeyType in keyof T]: T[KeyType]};

interface Field {
    name: string;
    widget: WidgetLike;
    label: string;
    help_text: string;
}

export interface FieldMap {
    [name: string]: Field;
}

export interface FormLike<T extends FieldMap> {
    name: string;
    fields: T;
    errors: {[P in keyof T]?: string[]} | null;
    iterator: Array<Extract<keyof T, string>>;
    prefix: string;
}

export interface FormSetLike<T extends FieldMap> {
    initial: number;
    total: number;
    max_num: number;
    min_num: number;
    can_delete: boolean;
    can_order: boolean;
    non_form_errors: string[];

    // Technically we don't need management form.
    // Since we have ManagementForm as a component that uses initial and total.
    management_form: unknown;
    prefix: string;

    forms: Array<FormLike<T>>;
    empty_form: FormLike<T>;
}

type ValueFromDatadict<T extends WidgetLike> = (
    widget: T,
) => T["value_from_datadict"];

type FilterMultiWidgets<T extends WidgetLike> = T extends {subwidgets: unknown}
    ? never
    : T extends {value: string | null; value_from_datadict: string | null}
    ? never
    : T extends {value_from_datadict: unknown}
    ? T["tag"]
    : never;

type Initializers = {
    [K in WidgetLike["tag"] as FilterMultiWidgets<
        DiscriminateUnion<WidgetLike, "tag", K>
    >]: ValueFromDatadict<DiscriminateUnion<WidgetLike, "tag", K>>;
};

const initializers: Initializers = {
    /*
    "django.forms.widgets.CheckboxInput": (widget) => {
        if (widget.attrs.checked === true) {
            return true;
        }
        return false;
    },
    "django.forms.widgets.Select": (widget) => {
        return widget.value[0];
    },
    "django.forms.widgets.SelectMultiple": (widget) => {
        return widget.value;
    },
    */
};

export type FormValues<U extends FieldMap> = Simplify<{
    [K in keyof U]: U[K] extends {enum: unknown} ? (U[K]["enum"] | null): U[K]["widget"]["value_from_datadict"];
}>;

const widgetToValue = <T extends WidgetLike>(prefix: string, name: string, widget: T) => {
    if (widget.subwidgets != null) {
        const subwidgetValue = Object.fromEntries(
            widget.subwidgets.map((subwidget) => {
                const formPrefix = prefix == "" ? "" : `${prefix}-`;
                const unprefixedName = subwidget.name.replace(
                    `${formPrefix}${name}_`,
                    "",
                );
                return widgetToValue(prefix, unprefixedName, subwidget);
            }),
        ) as Record<string, any>;
        return [name, subwidgetValue];
    } else if (widget.tag in initializers) {
        return [name, (initializers as any)[widget.tag](widget)];
    } else {
        return [name, widget.value];
    }
};

const getInitialValue = (widget: WidgetLike) => {
    if (widget.tag in initializers) {
        return (initializers as any)[widget.tag](widget);
    } else {
        return widget.value;
    }
};

const useInitialState = <T extends FieldMap>(form: FormLike<T>) => {
    const initialValuesAsEntries = form.iterator.map((fieldName) => {
        const field = form.fields[fieldName];
        const widget = field.widget;

        if (widget.subwidgets != null) {
            const subwidgetValue = Object.fromEntries(
                widget.subwidgets.map((subwidget) => {
                    const formPrefix = form.prefix == "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(
                        `${formPrefix}${fieldName}_`,
                        "",
                    );
                    return [unprefixedName, getInitialValue(subwidget)];
                }),
            );
            return [fieldName, subwidgetValue];
        }
        return [fieldName, getInitialValue(widget)];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<T>;
};

const bindField = (field: {label: string, error: string|null, value: any}, setValue: any, widget: WidgetLike) => {
    return {
        name: widget.name,
        tag: widget.tag,
        value: field.value,
        label: field.label,
        error: field.error,
        widget,
        handler: setValue,
    };
};

export type CreateFieldHandler<T> = T extends {tag: string; name: string; subwidgets: infer U}
    ? {
        tag: T["tag"];
        name: string;
        label: string;
        error: string | null;
        subwidgets: {[K in keyof U]: CreateFieldHandler<U[K]>};
    }
    : T extends WidgetLike
    ? {
        tag: T["tag"];
        name: string;
        value: T["value_from_datadict"];
        label: string;
        error: string | null;
        widget: T;
        handler: (value: T["value_from_datadict"]) => void;
    }
    : never;

export type FieldHandler<TWidget extends WidgetLike> = {
    [K in TWidget["tag"]]: CreateFieldHandler<
        DiscriminateUnion<TWidget, "tag", K>
    >;
}[TWidget["tag"]];

interface BaseFieldsProps<U extends FieldMap> {
    fieldInterceptor?: (form: FormLike<U>, fieldName: keyof U) => U[keyof U];
    changeInterceptor?: (
        name: keyof U,
        prevValues: FormValues<U>,
        nextValues: FormValues<U>,
    ) => FormValues<U>;
    form: FormLike<U> | FormHandler<U>;
    children: (
        props: FieldHandler<U[keyof U]["widget"]>,
    ) => React.ReactNode;
}

interface IncludeFieldsProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: Array<keyof U>;
    exclude?: never;
}

interface ExcludeFieldProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: never;
    exclude: Array<keyof U>;
}

export type FieldsProps<U extends FieldMap> = IncludeFieldsProps<U> | ExcludeFieldProps<U>;

export const Fields = <U extends FieldMap>(props: FieldsProps<U>) => {
    const getField =
        props.fieldInterceptor ?? ((form, fieldName) => form.fields[fieldName]);
    const defaultHandler = "setValues" in props.form ? props.form : useForm({form: props.form});
    const form = "setValues" in props.form ? props.form.form : props.form;

    const getIterator = () => {
        if (props.fields != null) {
            return props.fields;
        }

        if (props.exclude != null) {
            return form.iterator.filter(
                (field) => !props.exclude.includes(field),
            );
        }

        return form.iterator;
    };

    const iterator = getIterator();
    const handler = "setValues" in props.form ? props.form : defaultHandler;

    return (
        <>
            {iterator
                .map(
                    (fieldName) =>
                        [
                            fieldName,
                            // handler.fieldInterceptor(props.form, fieldName),
                            form.fields[fieldName]
                        ] as const,
                )
                .map(([fieldName, field]) => {
                    const {widget} = field;
                    const error = null; 
                    /*
                        handler.errors != null
                            ? handler.errors[fieldName] ?? null
                            : null;
                    */

                    return (
                        <React.Fragment key={fieldName.toString()}>
                            {props.children(fieldToHandler(handler, field))}
                        </React.Fragment>
                    );
                })}
        </>
    );
}

const fieldToHandler = <T extends FieldMap, TField extends T[keyof T]>(handler: FormHandler<T>, field: TField): FieldHandler<TField["widget"]> => {
    const fieldName = field.name;

    if (field.widget.subwidgets != null) {
        const subwidgets = field.widget.subwidgets.map((subwidget) => {
            const formPrefix = handler.form.prefix == "" ? "" : `${handler.form.prefix}-`;
            const unprefixedName = subwidget.name.replace(
                `${formPrefix}${fieldName}_`,
                "",
            );

            const subwidgetValues = handler.values[fieldName] as any;
            const subwidgetValue = subwidgetValues[unprefixedName];

            const setSubwidgetValue = (value: any) => {
                handler.setValues({
                    ...handler.values,
                    [fieldName]: {
                        ...subwidgetValues,
                        [unprefixedName]: value,
                    },
                });
            };

            return bindField({label: field.label, error: null, value: subwidgetValue}, setSubwidgetValue, {
                ...subwidget,
            });
        });

        return {
            name: fieldName,
            error: null,
            label: field.label,
            tag: field.widget.tag,
            subwidgets,
        } as any;
    }

    const value = handler.values[fieldName];
    const setValue = (value: any) => {
        handler.setValues({
            ...handler.values,
            [fieldName]: value,
        });
    };

    return bindField({label: field.label, error: null, value: handler.values[fieldName]}, setValue, field.widget) as any;
}

export interface FormHandler<T extends FieldMap> {
    form: FormLike<T>;
    values: FormValues<T>;
    setValues: React.Dispatch<React.SetStateAction<FormValues<T>>>;
    iterate: (callback: (field: FieldHandler<T[keyof T]["widget"]>) => React.ReactNode) => React.ReactNode[];
}

export const useForm = <T extends FieldMap>({form}: {form: FormLike<T>}): FormHandler<T> => {
    const initialState = useInitialState(form);
    const [values, setValues] = React.useState(initialState);

    const iterate = (callback: (field: FieldHandler<T[keyof T]["widget"]>) => React.ReactNode) => {
        return form.iterator.map((fieldName) => {
            const field = form.fields[fieldName];

            if (field.widget.subwidgets != null) {

                const subwidgets = field.widget.subwidgets.map((subwidget) => {
                    const formPrefix = form.prefix == "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(
                        `${formPrefix}${fieldName}_`,
                        "",
                    );

                    const subwidgetValues = values[fieldName] as any;
                    const subwidgetValue = subwidgetValues[unprefixedName];

                    const setSubwidgetValue = (value: any) => {
                        setValues({
                            ...values,
                            [fieldName]: {
                                ...subwidgetValues,
                                [unprefixedName]: value,
                            },
                        });
                    };

                    return bindField({label: field.label, error: null, value: subwidgetValue}, setSubwidgetValue, {
                        ...subwidget,
                    });
                });

                return callback({
                    name: fieldName,
                    tag: field.widget.tag,
                    subwidgets,
                } as any);
            }

            const value = values[fieldName];
            const setValue = (value: any) => {
                setValues({
                    ...values,
                    [fieldName]: value,
                });
            };

            return callback(
                bindField({label: field.label, error: null, value: values[fieldName]}, setValue, field.widget) as any,
            );
        });
    };
    
    return {
        form,
        values,
        setValues,
        iterate,
    }
}
export const Bar = (props: {widget: Types["Widget"]}) => {
    return <div>Ok</div>;
}

export const Widget = (props: {field: FieldHandler<Types["Widget"]>}) => {
    const {field} = props;

    if ("subwidgets" in field) {
        return (
            <React.Fragment key={field.name}>
                {field.subwidgets.map((subwidget) => {
                    return <Widget key={subwidget.name} field={subwidget} />;
                })}
            </React.Fragment>
        );
    }

    if (field.tag === "django.forms.widgets.HiddenInput") {
        return <input type="hidden" name={field.name} value={field.value ?? ""} />;
    } else if (field.tag === "django.forms.widgets.CheckboxInput") {
        return (
            <widgets.CheckboxInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
            />
        );
    } else if (
        field.tag === "django.forms.widgets.TextInput" ||
        field.tag == "django.forms.widgets.DateInput" ||
        field.tag == "django.forms.widgets.URLInput" ||
        field.tag == "django.forms.widgets.PasswordInput" ||
        field.tag == "django.forms.widgets.EmailInput" ||
        field.tag == "django.forms.widgets.TimeInput" ||
        field.tag == "django.forms.widgets.Textarea"
    ) {
        return (
            <widgets.TextInput name={field.name} value={field.value} onChange={field.handler} />
        );
    } else if (field.tag === "django.forms.widgets.Select") {
        return (
            <widgets.Select
                name={field.name}
                value={field.value}
                optgroups={field.widget.optgroups}
                onChange={field.handler}
            />
        );
    } else if (field.tag === "django.forms.widgets.ClearableFileInput") {
        return <input type="file" name={field.name} value={field.value ?? ""} />;
    } else if (field.tag === "django.forms.widgets.SelectMultiple") {
        return (
            <select
                name={field.name}
                multiple
                value={field.value}
                onChange={(event) => {
                    const value = Array.from(
                        event.target.selectedOptions,
                        (option) => option.value,
                    );
                    field.handler(value);
                }}
            >
                {field.widget.optgroups.map((optgroup) => {
                    const value = (optgroup[1][0].value ?? "").toString();
                    return (
                        <option key={value} value={value}>
                            {optgroup[1][0].label}
                        </option>
                    );
                })}
            </select>
        );
    }

    const exhastive: never = field;
    throw new Error(`Exhaustive`);
};

export const ManagementForm = <T extends FieldMap>({
    formSet,
}: {
    formSet: FormSetLike<T>;
}) => {
    return (
        <>
            <input
                type="hidden"
                name={`${formSet.prefix}-INITIAL_FORMS`}
                value={formSet.initial}
            />
            <input
                type="hidden"
                name={`${formSet.prefix}-TOTAL_FORMS`}
                value={formSet.total}
            />
        </>
    );
};

export const bindForms = <TContext extends {csrf_token: string}>(
    Context: React.Context<TContext>,
) => {
    const CSRFToken = (props: {}) => {
        const context = React.useContext(Context);

        return (
            <input
                type="hidden"
                name="csrfmiddlewaretoken"
                value={context.csrf_token}
            />
        );
    };

    const Form = <T extends FieldMap>(props: {form: FormLike<T>}) => {
        const form = useForm({form: props.form});

        return <>{form.iterate(field => <div key={field.name}><Widget field={field} /></div>)}</>;
    }

    return {
        ...widgets,
        Widget,
        CSRFToken,
        Form,
        useForm,
        ManagementForm,
        Fields,
    }
};