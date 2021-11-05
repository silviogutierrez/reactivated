import React from "react";
import {
    ReactivatedSerializationCheckboxInput,
    ReactivatedSerializationSelectDateWidget,
    ReactivatedSerializationSelect,
    ReactivatedSerializationTextInput,
    ReactivatedSerializationDateInput,
    ReactivatedSerializationTimeInput,
    ReactivatedSerializationSplitDateTimeWidget,
} from "@client/generated";
import { Formatters } from "tslint";

// Move to utilities?
type DiscriminateUnion<T, K extends keyof T, V extends T[K]> = T extends Record<K, V>
? T
: never;

type Simplify<T> = {[KeyType in keyof T]: T[KeyType]};

type Widget_GENERATEME =
    | ReactivatedSerializationCheckboxInput
    | ReactivatedSerializationSelectDateWidget
    | ReactivatedSerializationSelect
    | ReactivatedSerializationSplitDateTimeWidget
    | ReactivatedSerializationDateInput
    | ReactivatedSerializationTimeInput
    | ReactivatedSerializationTextInput;


interface Field {
    name: string;
    widget: Widget_GENERATEME;
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

type ValueFromDatadict<T extends Widget_GENERATEME> = (widget: T) => T["value_from_datadict"];

type FilterMultiWidgets<T extends Widget_GENERATEME> = T extends {subwidgets: unknown} ? never : T extends {value: string | null, value_from_datadict: string | null} ? never : T extends {value_from_datadict: unknown} ? T["tag"] : never;

type Initializers = {[K in Widget_GENERATEME["tag"] as FilterMultiWidgets<DiscriminateUnion<Widget_GENERATEME, "tag", K>>]: ValueFromDatadict<DiscriminateUnion<Widget_GENERATEME, "tag", K>>};

const initializers: Initializers = {
    "django.forms.widgets.CheckboxInput": (widget) => {
        if (widget.attrs.checked === true) {
            return true;
        }
        return false;
    },
    "django.forms.widgets.Select": (widget) => {
        return widget.value[0];
    },
};

export type FormValues<U extends FieldMap> = Simplify<{
    [K in keyof U]: U[K]["widget"]["value_from_datadict"]
}>;

const widgetToValue = (prefix: string, name: string, widget: Widget_GENERATEME) => {
    if ("subwidgets" in widget) {
        const subwidgetValue = Object.fromEntries(
            widget.subwidgets.map(subwidget => {
                const formPrefix = prefix == "" ? "" : `${prefix}-`;
                const unprefixedName = subwidget.name.replace(`${formPrefix}${name}_`, "");
                return widgetToValue(prefix, unprefixedName, subwidget);
            })
        ) as Record<string, any>;
        return [name, subwidgetValue];
    }
    else if (widget.tag in initializers) {
        return [name, (initializers as any)[widget.tag](widget)];
    }
    else {
        return [name, widget.value];
    }

}

const getInitialValue = (widget: Widget_GENERATEME) => {
    if (widget.tag in initializers) {
        return (initializers as any)[widget.tag](widget);
    }
    else {
        return widget.value;
    }
}

const useInitialState = <T extends FieldMap>(form: FormLike<T>) => {
    const initialValuesAsEntries = form.iterator.map((fieldName) => {
        // const field = fieldInterceptor(form, fieldName);
        const field = form.fields[fieldName];
        const widget = field.widget;

        if ("subwidgets" in widget) {
            const subwidgetValue = Object.fromEntries(
                widget.subwidgets.map(subwidget => {
                    const formPrefix = form.prefix == "" ? "" : `${form.prefix}-`;
                    const unprefixedName = subwidget.name.replace(`${formPrefix}${fieldName}_`, "");
                    return [unprefixedName, getInitialValue(subwidget)];
                })
            )
            return [fieldName, subwidgetValue];
        }
        return [fieldName, getInitialValue(widget)];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<
        T
    >;
}

type Thing<T> = T extends {tag: string, name: string, subwidgets: infer U} ? {
    tag: T["tag"];
    name: string;
    subwidgets: {[K in keyof U]: Thing<U[K]>};
} : T extends Widget_GENERATEME ? {
    tag: T["tag"];
    name: string;
    value: T["value_from_datadict"]; 
    widget: T,
    handler: (value: T["value_from_datadict"]) => void;
} : never;

type OuterTagged = {
    [K in Widget_GENERATEME["tag"]]: Thing<DiscriminateUnion<Widget_GENERATEME, "tag", K>>;
}[Widget_GENERATEME["tag"]];

export const useForm = <T extends FieldMap>({form}: {form: FormLike<T>}) => {
    const initialState = useInitialState(form);
    const [values, setValues] = React.useState(initialState);

    const bindField = (value: any, setValue: any, widget: Widget_GENERATEME) => {
        return {
            name: widget.name,
            tag: widget.tag,
            value: value,
            widget,
            handler: setValue,
        }
    }

    const iterate = (callback: (field: OuterTagged) => void) => {
        return form.iterator.map((fieldName) => {
            const field = form.fields[fieldName];

            if ("subwidgets" in field.widget) {
                return callback({
                    name: fieldName,
                    tag: field.widget.tag,
                    subwidgets: field.widget.subwidgets.map((subwidget) => {
                        const formPrefix = form.prefix == "" ? "" : `${form.prefix}-`;
                        const unprefixedName = subwidget.name.replace(`${formPrefix}${fieldName}_`, "");

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
                        }

                        return bindField(subwidgetValue, setSubwidgetValue, {
                            ...subwidget,
                        });
                    }) as any,
                });
            }

            const value = values[fieldName];
            const setValue = (value: any) => {
                setValues({
                    ...values,
                    [fieldName]: value,
                });
            }

            return callback(bindField(values[fieldName], setValue, field.widget) as any);
        });
    }


    return {values, initialState, setValues, iterate};
}

const CheckboxInput = (props: {name: string, value: true | false, onChange: (value: boolean) => void}) => {
    return (
        <input
            type="checkbox"
            name={props.name}
            checked={props.value}
            onChange={(event) => props.onChange(event.target.checked)}
        />
    );
}

const TextInput = (props: {name: string, value: string | null, onChange: (value: string) => void}) => {
    return (
        <input
            type="text"
            name={props.name}
            value={props.value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        />
    );
}

const Select = (props: {name: string, value: string | number | null, optgroups: ReactivatedSerializationSelect["optgroups"], onChange: (value: string) => void}) => {
    const {name, optgroups, value} = props;

    return <select key={name} name={name} value={value ?? ""} onChange={(event) => props.onChange(event.target.value)}>
        {optgroups.map(optgroup =>  {
            const value = (optgroup[1][0].value ?? "").toString();
            return <option key={value} value={value}>{optgroup[1][0].label}</option>
        }
        )}
    </select>
}

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

    if (field.tag === "django.forms.widgets.CheckboxInput") {
        return <CheckboxInput name={field.name} value={field.value} onChange={field.handler} />
    }
    else if (field.tag === "django.forms.widgets.TextInput" || field.tag == "django.forms.widgets.DateInput" || field.tag == "django.forms.widgets.TimeInput") {
        return (
            <TextInput
                name={field.name}
                value={field.value}
                onChange={field.handler}
            />
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
    }

    const exhastive: never = field;
    throw new Error(`Exhaustive`);
}

export const Form = <T extends FieldMap>(props: {form: FormLike<T>}) => {
    const form = useForm(props);

    const rendered = form.iterate((field) => <Widget key={field.name} field={field} />);

    return <div>
        {rendered}
        <h1>Form initial</h1>
        <pre>{JSON.stringify(form.initialState, null, 2)}</pre>
        <h1>Form state</h1>
        <pre>{JSON.stringify(form.values, null, 2)}</pre>
    </div>

}