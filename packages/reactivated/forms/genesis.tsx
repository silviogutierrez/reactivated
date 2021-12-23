import React from "react";
import * as widgets from "./widgets";
import produce, {castDraft} from "immer";
import {Types} from "../generated";

export type Optgroup = Types["Optgroup"];

// TODO: move to utilities.
type DiscriminateUnion<T, K extends keyof T, V extends T[K]> = T extends Record<K, V>
    ? T
    : never;

export interface WidgetLike {
    name: string;
    tag: string;
    attrs: {
        disabled?: boolean;
        id: string;
    };
    subwidgets?: WidgetLike[];
    value: unknown;
}

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
    initial_form_count: number;
    total_form_count: number;
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

export type FormValues<U extends FieldMap> = {
    [K in keyof U]: U[K] extends {enum: unknown}
        ? U[K]["enum"] | null
        : U[K]["widget"] extends {_reactivated_value_do_not_use?: unknown}
        ? NonNullable<U[K]["widget"]["_reactivated_value_do_not_use"]>
        : U[K]["widget"]["value"];
};

export interface FormHandler<T extends FieldMap> {
    form: FormLike<T>;
    values: FormValues<T>;
    iterate: (
        iterator: Array<Extract<keyof T, string>>,
        callback: (field: FieldHandler<T[keyof T]["widget"]>) => React.ReactNode,
    ) => React.ReactNode[];
}

export const getInitialFormState = <T extends FieldMap>(form: FormLike<T>) => {
    const initialValuesAsEntries = form.iterator.map((fieldName) => {
        const field = form.fields[fieldName];
        const widget = field.widget;

        if (widget.subwidgets != null) {
            const subwidgetValue = Object.fromEntries(
                widget.subwidgets.map((subwidget) => {
                    const formPrefix = form.prefix === "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(
                        `${formPrefix}${fieldName}_`,
                        "",
                    );
                    return [unprefixedName, subwidget.value];
                }),
            );
            return [fieldName, subwidgetValue];
        }
        return [fieldName, widget.value];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<T>;
};

export const getInitialFormSetState = <U extends FieldMap>(forms: FormLike<U>[]) => {
    return Object.fromEntries(
        forms.map((form) => [form.prefix, getInitialFormState(form)] as const),
    );
};

export const getFormHandler = <T extends FieldMap>({
    form,
    values,
    setValues,
    ...options
}: {
    form: FormLike<T>;
    values: FormValues<T>;
    setValues: React.Dispatch<React.SetStateAction<FormValues<T>>>;
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<T[keyof T]["widget"]>,
        values: FormValues<T>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
}): FormHandler<T> => {
    const changeInterceptor =
        options.changeInterceptor ?? ((_, prevValues, nextValues) => nextValues);
    const fieldInterceptor = options.fieldInterceptor ?? ((fieldName, field) => field);

    const changeValues = (fieldName: keyof T, incomingValues: any) => {
        setValues((prevValues) => {
            const nextValues = changeInterceptor(fieldName, prevValues, incomingValues);
            return nextValues;
        });
    };

    const iterate = (
        iterator: Array<Extract<keyof T, string>>,
        callback: (field: FieldHandler<T[keyof T]["widget"]>) => React.ReactNode,
    ) => {
        return iterator.map((fieldName) => {
            const field = form.fields[fieldName];
            const error = form.errors?.[fieldName]?.[0] ?? null;

            if (field.widget.subwidgets != null) {
                const subwidgets = field.widget.subwidgets.map((subwidget) => {
                    const formPrefix = form.prefix === "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(
                        `${formPrefix}${fieldName}_`,
                        "",
                    );
                    const subwidgetValues = values[fieldName] as any;
                    const subwidgetValue = subwidgetValues[unprefixedName];
                    const setSubwidgetValue = (value: unknown) => {
                        changeValues(fieldName, {
                            ...values,
                            [fieldName]: {
                                ...subwidgetValues,
                                [unprefixedName]: value,
                            },
                        });
                    };
                    const fieldHandler: FieldHandler<any> = {
                        name: subwidget.name,
                        error,
                        label: field.label,
                        disabled: false,
                        tag: subwidget.tag,
                        widget: subwidget,
                        value: subwidgetValue,
                        handler: setSubwidgetValue,
                    };
                    return fieldHandler;
                });

                return callback(
                    fieldInterceptor(
                        fieldName,
                        {
                            name: field.widget.name,
                            disabled: field.widget.attrs.disabled ?? false,
                            label: field.label,
                            error,
                            tag: field.widget.tag,
                            subwidgets,
                        } as any,
                        values,
                    ),
                );
            }

            const fieldHandler: FieldHandler<any> = {
                name: field.widget.name,
                error,
                label: field.label,
                disabled: field.widget.attrs.disabled ?? false,
                tag: field.widget.tag,
                widget: field.widget,
                value: values[fieldName],
                handler: (value) => {
                    changeValues(fieldName, {
                        ...values,
                        [fieldName]: value,
                    });
                },
            };

            return callback(fieldInterceptor(fieldName, fieldHandler as any, values));
        });
    };

    return {form, values, iterate};
};

export const useForm = <T extends FieldMap>({
    form,
    ...options
}: {
    form: FormLike<T>;
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<T[keyof T]["widget"]>,
        values: FormValues<T>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
}): FormHandler<T> => {
    const initialState = getInitialFormState(form);
    const [values, setValues] = React.useState(initialState);

    return getFormHandler({...options, form, values, setValues});
};

export type CreateFieldHandler<T> = T extends {
    tag: string;
    name: string;
    subwidgets: infer U;
}
    ? {
          tag: T["tag"];
          name: string;
          label: string;
          error: string | null;
          disabled: boolean;
          subwidgets: {[K in keyof U]: CreateFieldHandler<U[K]>};
      }
    : T extends WidgetLike
    ? {
          tag: T["tag"];
          name: string;
          value: T["value"];
          label: string;
          error: string | null;
          disabled: boolean;
          widget: T;
          handler: (value: T["value"]) => void;
      }
    : never;

export type FieldHandler<TWidget extends WidgetLike> = {
    [K in TWidget["tag"]]: CreateFieldHandler<DiscriminateUnion<TWidget, "tag", K>>;
}[TWidget["tag"]];

interface BaseFieldsProps<T extends FieldMap> {
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<T[keyof T]["widget"]>,
        values: FormValues<T>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
    form: FormLike<T> | FormHandler<T>;
    children: (props: FieldHandler<T[keyof T]["widget"]>) => React.ReactNode;
}

interface IncludeFieldsProps<T extends FieldMap> extends BaseFieldsProps<T> {
    fields?: Array<Extract<keyof T, string>>;
    exclude?: never;
}

interface ExcludeFieldProps<T extends FieldMap> extends BaseFieldsProps<T> {
    fields?: never;
    exclude: Array<Extract<keyof T, string>>;
}

export type FieldsProps<T extends FieldMap> =
    | IncludeFieldsProps<T>
    | ExcludeFieldProps<T>;

export const Fields = <U extends FieldMap>(props: FieldsProps<U>) => {
    const defaultHandler =
        "form" in props.form
            ? props.form
            : useForm({form: props.form, changeInterceptor: props.changeInterceptor});
    const handler = "form" in props.form ? props.form : defaultHandler;

    const getIterator = () => {
        if (props.fields != null) {
            return props.fields;
        }

        if (props.exclude != null) {
            return handler.form.iterator.filter(
                (field) => !props.exclude.includes(field),
            );
        }

        return handler.form.iterator;
    };

    return (
        <>
            {handler.iterate(getIterator(), (field) => (
                <React.Fragment key={field.name}>
                    {props.children(field)}
                </React.Fragment>
            ))}
        </>
    );
};

export const Widget = (props: {field: FieldHandler<widgets.CoreWidget>}) => {
    const {field} = props;

    if ("subwidgets" in field) {
        return (
            <>
                {field.subwidgets.map((subwidget) => {
                    return <Widget key={subwidget.name} field={subwidget} />;
                })}
            </>
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
        field.tag === "django.forms.widgets.DateInput" ||
        field.tag === "django.forms.widgets.URLInput" ||
        field.tag === "django.forms.widgets.PasswordInput" ||
        field.tag === "django.forms.widgets.EmailInput" ||
        field.tag === "django.forms.widgets.TimeInput" ||
        field.tag === "django.forms.widgets.NumberInput" ||
        field.tag === "django.forms.widgets.Textarea"
    ) {
        return (
            <widgets.TextInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
            />
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
    throw new Error(`Exhaustive {field.tag}`);
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
                value={formSet.initial_form_count}
            />
            <input
                type="hidden"
                name={`${formSet.prefix}-TOTAL_FORMS`}
                value={formSet.total_form_count}
            />
        </>
    );
};

export const useFormSet = <T extends FieldMap>(options: {
    formSet: FormSetLike<T>;
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<T[keyof T]["widget"]>,
        values: FormValues<T>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
}) => {
    const [formSet, setFormSet] = React.useState(options.formSet);

    const initialFormSetState = getInitialFormSetState(options.formSet.forms);
    const [values, formSetSetValues] =
        React.useState<Partial<typeof initialFormSetState>>(initialFormSetState);

    const emptyFormValues = getInitialFormState(formSet.empty_form);

    const handlers = formSet.forms.map((form) => {
        return getFormHandler({
            form,
            changeInterceptor: options.changeInterceptor,
            fieldInterceptor: options.fieldInterceptor,
            values: values[form.prefix] ?? emptyFormValues,
            setValues: (incomingValuesCallback) => {
                formSetSetValues((prevValues) => {
                    const nextValues = (incomingValuesCallback as any)(
                        prevValues[form.prefix],
                    );
                    return {
                        ...prevValues,
                        [form.prefix]: nextValues,
                    };
                });
            },
        });
    });

    const addForm = () => {
        const {total_form_count} = formSet;
        type AdditionalForm = typeof formSet["forms"][number];

        const extraForm = produce(formSet.empty_form, (draftState) => {
            for (const fieldName of draftState.iterator) {
                const prefix = `${formSet.prefix}-${formSet.total_form_count}`;
                const field = draftState.fields[fieldName];
                const html_name = `${prefix}-${field.name}`;
                draftState.fields[fieldName].widget.name = html_name;
                draftState.fields[fieldName].widget.attrs.id = `id_${html_name}`;
                draftState.prefix = prefix;
            }
        });
        const updated = produce(formSet, (draftState) => {
            draftState.forms.push(castDraft(extraForm));
            draftState.total_form_count += 1;
        });

        setFormSet(updated);
    };

    return {schema: formSet, values, handlers, addForm};
};
