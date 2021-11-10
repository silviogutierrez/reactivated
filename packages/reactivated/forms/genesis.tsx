import React from "react";

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
        // const field = fieldInterceptor(form, fieldName);
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

const bindField = (value: any, setValue: any, widget: WidgetLike) => {
    return {
        name: widget.name,
        tag: widget.tag,
        value: value,
        widget,
        handler: setValue,
    };
};


export const bindUseForm = <TWidget extends WidgetLike>() => {
    type CreateFieldHandler<T> = T extends {tag: string; name: string; subwidgets: infer U}
        ? {
            tag: T["tag"];
            name: string;
            subwidgets: {[K in keyof U]: CreateFieldHandler<U[K]>};
        }
        : T extends TWidget
        ? {
            tag: T["tag"];
            name: string;
            value: T["value_from_datadict"];
            widget: T;
            handler: (value: T["value_from_datadict"]) => void;
        }
        : never;

    type FieldHandler = {
        [K in TWidget["tag"]]: CreateFieldHandler<
            DiscriminateUnion<TWidget, "tag", K>
        >;
    }[TWidget["tag"]];

    const useForm = <T extends FieldMap>({form}: {form: FormLike<T>}) => {
        const initialState = useInitialState(form);
        const [values, setValues] = React.useState(initialState);


        return {
            values,
            setValues,
        }

        const iterate = (callback: (field: FieldHandler) => void) => {
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

                        return bindField(subwidgetValue, setSubwidgetValue, {
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
                    bindField(values[fieldName], setValue, field.widget) as any,
                );
            });
        };
    }

    return useForm;
}

/*
export const Widget = (props: {field: OuterTagged}) => {
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
            <CheckboxInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
            />
        );
    } else if (
        field.tag === "django.forms.widgets.TextInput" ||
        field.tag == "django.forms.widgets.DateInput" ||
        field.tag == "django.forms.widgets.TimeInput"
    ) {
        return (
            <TextInput name={field.name} value={field.value} onChange={field.handler} />
        );
    } else if (field.tag === "django.forms.widgets.Select") {
        return (
            <Select
                name={field.name}
                value={field.value}
                optgroups={field.widget.optgroups}
                onChange={field.handler}
            />
        );
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
*/