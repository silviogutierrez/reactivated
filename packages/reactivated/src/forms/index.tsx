import {produce, castDraft} from "immer";
import {FileInfoResult} from "prettier";
import React from "react";

import {DjangoFormsWidgetsHiddenInput, Types} from "../generated";
import {DiscriminateUnion} from "../types";
import * as widgets from "./widgets";

export type Optgroup = Types["Optgroup"];

export interface WidgetLike {
    name: string;
    tag: string;
    is_hidden: boolean;
    attrs: {
        disabled?: boolean;
        id: string;
    };
    subwidgets?: WidgetLike[];
    value: unknown;
}

interface FieldLike<W = WidgetLike> {
    name: string;
    widget: W;
    label: string;
    help_text: string | null;
}

export interface FieldMap<W = WidgetLike> {
    [name: string]: FieldLike<W>;
}

export interface FormLike<T extends FieldMap<W>, W = WidgetLike> {
    name: string;
    fields: T;
    errors: {[P in keyof T]?: string[]} | null;
    iterator: Array<Extract<keyof T, string>>;
    prefix: string;
}

export interface FormSetLike<T extends FieldMap<W>, W = WidgetLike> {
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

    forms: Array<FormLike<T, W>>;
    empty_form: FormLike<T, W>;
}

export type FormErrors<T extends FieldMap> = {[P in keyof T]?: string[]} | null;

export type FormValues<T extends FieldMap> = {
    [K in keyof T]: T[K] extends {enum: unknown}
        ? T[K]["enum"] | null
        : T[K]["widget"] extends {_reactivated_value_do_not_use?: unknown}
        ? NonNullable<T[K]["widget"]["_reactivated_value_do_not_use"]>
        : T[K]["widget"]["value"];
};

export interface FormHandler<T extends FieldMap> {
    form: FormLike<T>;
    values: FormValues<T>;
    initial: FormValues<T>;
    errors: FormErrors<T>;

    fields: {[K in keyof T]: FieldHandler<T[keyof T]["widget"]>};
    visibleFields: FieldHandler<T[keyof T]["widget"]>[];
    hiddenFields: FieldHandler<DjangoFormsWidgetsHiddenInput>[];
    nonFieldErrors: string[] | null;

    setValue: <K extends keyof T>(name: K, value: FormValues<T>[K]) => void;
    setValues: (values: FormValues<T>) => void;
    setErrors: (errors: FormErrors<T>) => void;
    iterate: (
        iterator: Array<Extract<keyof T, string>>,
        callback: (
            fieldName: keyof T,
            field: FieldHandler<T[keyof T]["widget"]>,
        ) => React.ReactNode,
    ) => React.ReactNode[];
    reset: () => void;
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

export const getInitialFormSetState = <T extends FieldMap>(
    forms: Array<FormLike<T>>,
    initial?: FormValues<T>[],
) => {
    return forms.map((form, index) => initial?.[index] ?? getInitialFormState(form));
};

export const getInitialFormSetErrors = <T extends FieldMap>(
    forms: Array<FormLike<T>>,
) => {
    return Object.fromEntries(forms.map((form) => [form.prefix, form.errors] as const));
};

export const getFormHandler = <T extends FieldMap>({
    form,
    values,
    initial,
    errors,
    setValues,
    setErrors,
    ...options
}: {
    form: FormLike<T>;
    values: FormValues<T>;
    initial: FormValues<T>;
    errors: FormErrors<T>;
    setErrors: (errors: FormErrors<T>) => void;
    setValues: (
        getValuesToSetFromPrevValues: (values: FormValues<T>) => FormValues<T>,
    ) => void;
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

    const changeValues = (
        fieldName: keyof T,
        getIncomingValues: (prevValues: FormValues<T>) => FormValues<T>,
    ) => {
        setValues((prevValues) => {
            const incomingValues = getIncomingValues(prevValues);
            const nextValues = changeInterceptor(fieldName, prevValues, incomingValues);
            return nextValues;
        });
    };

    const reset = () => {
        setValues(() => initial);
        setErrors({});
    };

    const fields = Object.fromEntries(
        form.iterator.map((fieldName) => {
            const field = form.fields[fieldName];
            const error = errors?.[fieldName]?.[0] ?? null;
            const {help_text} = field;

            if (field.widget.subwidgets != null) {
                const subwidgets = field.widget.subwidgets.map((subwidget) => {
                    const formPrefix = form.prefix === "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(
                        `${formPrefix}${fieldName}_`,
                        "",
                    );

                    const setSubwidgetValue = (value: unknown) => {
                        changeValues(fieldName, (prevValues) => {
                            const subwidgetValues = prevValues[fieldName] as any;
                            const subwidgetValue = subwidgetValues[unprefixedName];

                            return {
                                ...prevValues,
                                [fieldName]: {
                                    ...subwidgetValues,
                                    [unprefixedName]: value,
                                },
                            };
                        });
                    };
                    const subfieldHandler: WidgetHandler<any> = {
                        name: subwidget.name,
                        error,
                        help_text,
                        label: field.label,
                        disabled: false,
                        tag: subwidget.tag,
                        widget: subwidget,
                        value: (values[fieldName] as any)[unprefixedName],
                        handler: setSubwidgetValue,
                    };
                    return subfieldHandler;
                });

                const subwidgetHandler: SubwidgetHandler<
                    typeof field.widget,
                    typeof field.widget.subwidgets
                > = {
                    name: field.widget.name,
                    disabled: field.widget.attrs.disabled ?? false,
                    label: field.label,
                    error,
                    help_text,
                    tag: field.widget.tag,
                    subwidgets,
                };

                return [
                    fieldName,
                    fieldInterceptor(
                        fieldName,
                        subwidgetHandler as FieldHandler<T[keyof T]["widget"]>,
                        values,
                    ),
                ] as const;
            }

            const fieldHandler: WidgetHandler<typeof field.widget> = {
                name: field.widget.name,
                error,
                help_text,
                label: field.label,
                disabled: field.widget.attrs.disabled ?? false,
                tag: field.widget.tag,
                widget: field.widget,
                value: values[fieldName],
                handler: (value) => {
                    changeValues(fieldName, (prevValues) => ({
                        ...prevValues,
                        [fieldName]: value,
                    }));
                },
            };

            return [
                fieldName,
                fieldInterceptor(
                    fieldName,
                    fieldHandler as FieldHandler<T[keyof T]["widget"]>,
                    values,
                ),
            ] as const;
        }),
    ) as FormHandler<T>["fields"];

    const iterate = (
        iterator: Array<Extract<keyof T, string>>,
        callback: (
            fieldName: keyof T,
            field: FieldHandler<T[keyof T]["widget"]>,
        ) => React.ReactNode,
    ) => {
        return iterator.map((fieldName) => {
            return callback(fieldName, fields[fieldName]);
        });
    };

    const visibleFields: FormHandler<T>["visibleFields"] = form.iterator
        .filter(
            (fieldName) => fields[fieldName].tag !== "django.forms.widgets.HiddenInput",
        )
        .map((fieldName) => fields[fieldName]);

    const hiddenFields: FormHandler<T>["hiddenFields"] = form.iterator
        .filter(
            (fieldName) => fields[fieldName].tag === "django.forms.widgets.HiddenInput",
        )
        .map(
            (fieldName) =>
                fields[
                    fieldName
                ] as unknown as FieldHandler<DjangoFormsWidgetsHiddenInput>,
        );
    const nonFieldErrors = errors?.["__all__"] ?? null;

    return {
        form,
        values,
        initial,
        errors,
        fields,
        nonFieldErrors,
        visibleFields,
        hiddenFields,
        iterate,
        reset,
        setErrors,
        setValues: (values) => {
            setValues(() => values);
        },
        setValue: (fieldName, value) => {
            changeValues(fieldName, (prevValues) => ({
                ...prevValues,
                [fieldName]: value,
            }));
        },
    };
};

export const useForm = <
    T extends FieldMap,
    S extends Array<keyof T> = [],
    R extends {[P in Exclude<keyof T, S[number]>]: T[P]} = {
        [P in Exclude<keyof T, S[number]>]: T[P];
    },
>(options: {
    form: FormLike<T>;
    initial?: Partial<FormValues<R>>;
    exclude?: [...S];
    fieldInterceptor?: (
        fieldName: keyof R,
        field: FieldHandler<R[keyof R]["widget"]>,
        values: FormValues<R>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof R,
        prevValues: FormValues<R>,
        nextValues: FormValues<R>,
    ) => FormValues<R>;
}): FormHandler<R> => {
    const form = {
        ...(options.form as any as FormLike<R>),
        iterator: options.form.iterator.filter(
            (field) => options.exclude == null || !options.exclude.includes(field),
        ),
    } as any as FormLike<R>;
    const initial = {...getInitialFormState(form), ...options.initial};
    const [values, formSetValues] = React.useState(initial);
    const [errors, setErrors] = React.useState(form.errors);

    return getFormHandler({
        ...options,
        form,
        errors,
        setErrors,
        initial,
        values,
        setValues: (getValuesToSetFromPrevValues) => {
            formSetValues((prevValues) => getValuesToSetFromPrevValues(prevValues));
        },
    });
};

export type CreateFieldHandler<T> = T extends {
    tag: string;
    name: string;
    subwidgets: infer U;
}
    ? SubwidgetHandler<T, U>
    : T extends WidgetLike
    ? WidgetHandler<T>
    : never;

export interface SubwidgetHandler<T extends {tag: string; name: string}, U> {
    tag: T["tag"];
    name: string;
    label: string;
    error: string | null;
    help_text: string | null;
    disabled: boolean;
    subwidgets: {[K in keyof U]: U[K] extends WidgetLike ? WidgetHandler<U[K]> : never};
}

export interface WidgetHandler<T extends WidgetLike> {
    tag: T["tag"];
    name: string;
    value: T["value"];
    label: string;
    error: string | null;
    help_text: string | null;
    disabled: boolean;
    widget: T;
    handler: (value: T["value"]) => void;
}

export type FieldHandler<TWidget extends WidgetLike> = {
    [K in TWidget["tag"]]: CreateFieldHandler<DiscriminateUnion<TWidget, "tag", K>>;
}[TWidget["tag"]];

interface BaseRendererProps<T extends FieldMap, F extends WidgetLike> {
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<F>,
        values: FormValues<T>,
    ) => typeof field;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
    form: FormLike<T> | FormHandler<T>;
    children: (field: FieldHandler<F>) => React.ReactNode;
}

interface IncludeRendererProps<T extends FieldMap, F extends WidgetLike>
    extends BaseRendererProps<T, F> {
    fields?: Array<Extract<keyof T, string>>;
    exclude?: never;
}

interface ExcludeRendererProps<T extends FieldMap, F extends WidgetLike>
    extends BaseRendererProps<T, F> {
    fields?: never;
    exclude: Array<Extract<keyof T, string>>;
}

export type RendererProps<T extends FieldMap, F extends WidgetLike> =
    | IncludeRendererProps<T, F>
    | ExcludeRendererProps<T, F>;

export const createIterator =
    <F extends WidgetLike>() =>
    <U extends FieldMap>(props: RendererProps<U, F>) => {
        const defaultHandler =
            "form" in props.form
                ? props.form
                : useForm({
                      form: props.form,
                      changeInterceptor: props.changeInterceptor,
                  });
        const handler = "form" in props.form ? props.form : defaultHandler;
        const fieldInterceptor =
            props.fieldInterceptor ?? ((fieldName, field, values) => field);

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
                {handler.iterate(getIterator(), (fieldName, field) => (
                    <React.Fragment key={field.name}>
                        {props.children(
                            fieldInterceptor(fieldName, field as any, handler.values),
                        )}
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
    } else if (field.tag === "django.forms.widgets.Textarea") {
        return (
            <widgets.Textarea
                name={field.name}
                value={field.value}
                onChange={field.handler}
            />
        );
    } else if (field.tag === "django.forms.widgets.PasswordInput") {
        return (
            <widgets.TextInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
                type="password"
            />
        );
    } else if (
        field.tag === "django.forms.widgets.TextInput" ||
        field.tag === "django.forms.widgets.DateInput" ||
        field.tag === "django.forms.widgets.URLInput" ||
        field.tag === "django.forms.widgets.EmailInput" ||
        field.tag === "django.forms.widgets.TimeInput" ||
        field.tag === "django.forms.widgets.NumberInput"
    ) {
        return (
            <widgets.TextInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
                placeholder={field.widget.attrs.placeholder}
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
    onAddForm?: (form: FormLike<T>) => void;
    initial?: FormValues<T>[];
    fieldInterceptor?: (
        fieldName: keyof T,
        field: FieldHandler<T[keyof T]["widget"]>,
        values: FormValues<T>,
    ) => FieldHandler<T[keyof T]["widget"]>;
    changeInterceptor?: (
        name: keyof T,
        prevValues: FormValues<T>,
        nextValues: FormValues<T>,
    ) => FormValues<T>;
}) => {
    const createForm = (index: number) => {
        return produce(options.formSet.empty_form, (draftState) => {
            for (const fieldName of draftState.iterator) {
                const prefix = `${options.formSet.prefix}-${index}`;
                const field = draftState.fields[fieldName];
                const htmlName = `${prefix}-${field.name}`;
                draftState.fields[fieldName].widget.name = htmlName;
                draftState.fields[fieldName].widget.attrs.id = `id_${htmlName}`;
                draftState.prefix = prefix;
            }
        });
    };

    const formSetFromInitialValues = produce(options.formSet, (draftState) => {
        if (options.initial == null) {
            return;
        }
        draftState.total_form_count = options.initial.length;
        draftState.forms = options.initial.map((_, index) => {
            return castDraft(createForm(index));
        });
    });

    const [formSet, setFormSet] = React.useState(formSetFromInitialValues);

    const initialFormSetState = getInitialFormSetState(
        formSetFromInitialValues.forms,
        options.initial,
    );
    const initialFormSetErrors = getInitialFormSetErrors(options.formSet.forms);
    const [values, formSetSetValues] =
        React.useState<typeof initialFormSetState>(initialFormSetState);
    const [errors, formSetSetErrors] =
        React.useState<typeof initialFormSetErrors>(initialFormSetErrors);

    const emptyFormValues = getInitialFormState(formSet.empty_form);

    const forms = formSet.forms.map((form, index) => {
        return getFormHandler({
            form,
            changeInterceptor: options.changeInterceptor,
            fieldInterceptor: options.fieldInterceptor,
            values: values[index] ?? emptyFormValues,
            errors: errors[index] ?? {},
            setErrors: (nextErrors) => {
                formSetSetErrors((prevErrors) => ({
                    ...prevErrors,
                    [index]: nextErrors,
                }));
            },
            initial: initialFormSetState[index] ?? emptyFormValues,
            setValues: (getValuesToSetFromPrevValues) => {
                formSetSetValues((prevValues) => {
                    const nextValues = getValuesToSetFromPrevValues(
                        prevValues[index] ?? emptyFormValues,
                    );
                    return produce(prevValues, (draftState) => {
                        draftState[index] = castDraft(nextValues);
                    });
                });
            },
        });
    });

    const addForm = () => {
        const {total_form_count} = formSet;

        const extraForm = createForm(formSet.total_form_count);

        const updated = produce(formSet, (draftState) => {
            draftState.forms.push(castDraft(extraForm));
            draftState.total_form_count += 1;
        });

        setFormSet(updated);
        options.onAddForm?.(extraForm);
    };

    return {schema: formSet, values, forms, addForm};
};

export const bindWidgetType = <W extends WidgetLike>() => {
    const Iterator = createIterator<W>();

    function createRenderer<TProps = Record<never, never>>(
        callback: (field: FieldHandler<W>, props: TProps) => React.ReactNode,
    ) {
        const Renderer = <T extends FieldMap>(props: TProps & RendererProps<T, W>) => {
            return <Iterator {...props}>{(field) => callback(field, props)}</Iterator>;
        };
        // This is not used, but here so that children is excluded from required props.
        Renderer.defaultProps = {
            children: () => null,
        };
        return Renderer;
    }

    return {
        createRenderer,
        Iterator,
    };
};

export const createCSRFToken = <TContext extends {csrf_token: string}>(
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
    return CSRFToken;
};

export const Form = <T extends FieldMap<widgets.CoreWidget>>(props: {
    form: FormLike<T> | FormHandler<T>;
    as: "p" | "table";
}) => {
    const form = "form" in props.form ? props.form : useForm({form: props.form});

    if (props.as == "p") {
        return (
            <>
                {form.nonFieldErrors?.map((error, index) => (
                    <div key={index}>{error}</div>
                ))}
                {form.hiddenFields.map((field, index) => (
                    <Widget key={index} field={field} />
                ))}
                {form.visibleFields.map((field, index) => (
                    <React.Fragment key={field.name}>
                        {field.error != null && <div>{field.error}</div>}
                        <p>
                            <label>{field.label}</label>
                            {field.help_text != null && <span>{field.help_text}</span>}
                            <Widget field={field} />
                        </p>
                    </React.Fragment>
                ))}
            </>
        );
    } else {
        return (
            <>
                {form.nonFieldErrors != null && (
                    <tr>
                        {form.nonFieldErrors.map((error, index) => (
                            <td key={index} colSpan={2}>
                                {error}
                            </td>
                        ))}
                    </tr>
                )}
                <tr style={{display: "none"}}>
                    {form.hiddenFields.map((field, index) => (
                        <Widget key={index} field={field} />
                    ))}
                </tr>
                {form.visibleFields.map((field, index) => (
                    <tr key={field.name}>
                        <th>
                            <label>{field.label}</label>
                        </th>
                        <td>
                            {field.error != null && <div>{field.error}</div>}
                            {field.help_text != null && (
                                <>
                                    <br />
                                    <span>{field.help_text}</span>
                                </>
                            )}
                            <Widget field={field} />
                        </td>
                    </tr>
                ))}
            </>
        );
    }
};

export const FormSet = <T extends FieldMap<widgets.CoreWidget>>(props: {
    formSet: FormSetLike<T>;
    as: "p" | "table";
}) => {
    return (
        <>
            <ManagementForm formSet={props.formSet} />
            {props.formSet.forms.map((form) => (
                <Form key={form.prefix} form={form} as={props.as} />
            ))}
        </>
    );
};

export type UnknownFormValues<T extends FieldMap> = {
    [K in keyof T]: T[K] extends {enum: unknown} ? T[K]["enum"] | null : unknown;
};

// TODO: Should be T extends Record<string, FormLike<any> | FormSetLike<any>>
// but jsonschema outputs interfaces instead of types. Figure out how to output a type.
export type FormOrFormSetValues<T> = T extends {tag: "FormGroup"}
    ? Omit<{[K in keyof T]: FormOrFormSetValues<T[K]>}, "tag">
    : T extends FormLike<any>
    ? UnknownFormValues<T["fields"]>
    : T extends FormSetLike<any>
    ? Array<UnknownFormValues<T["empty_form"]["fields"]>>
    : T extends null
    ? null
    : never;

export type FormOrFormSetErrors<T> = T extends {tag: "FormGroup"}
    ? Omit<{[K in keyof T]: FormOrFormSetErrors<T[K]>}, "tag">
    : T extends FormLike<any>
    ? NonNullable<T["errors"]>
    : T extends FormSetLike<any>
    ? Array<NonNullable<T["empty_form"]["errors"]>>
    : T extends null
    ? null
    : never;
