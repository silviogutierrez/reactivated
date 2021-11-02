import React from "react";
import {
    ReactivatedSerializationCheckboxInput,
    ReactivatedSerializationSelectDateWidget,
    ReactivatedSerializationSelect,
    ReactivatedSerializationTextInput,
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

type Initializers = {[K in Widget_GENERATEME["tag"]]: (widget: DiscriminateUnion<Widget_GENERATEME, "tag", K>) => DiscriminateUnion<Widget_GENERATEME, "tag", K>["value_from_datadict"]}

type WidgetValues = {[K in Widget_GENERATEME["tag"]]: {tag: K, value: DiscriminateUnion<Widget_GENERATEME, "tag", K>["value_from_datadict"]}}[Widget_GENERATEME["tag"]];

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
    "django.forms.widgets.SelectDateWidget": (widget) => {
        return widget.value;
    },
    "django.forms.widgets.TextInput": (widget) => {
        return widget.value;
    },
};

export type FormValues<U extends FieldMap> = Simplify<{
    [K in keyof U]: U[K]["widget"]["value_from_datadict"]
}>;

const useInitialState = <T extends FieldMap>(form: FormLike<T>) => {
    const initialValuesAsEntries = form.iterator.map((fieldName) => {
        // const field = fieldInterceptor(form, fieldName);
        const field = form.fields[fieldName];
        const widget = field.widget;
        widget.tag

        const value = initializers[widget.tag](widget as any);
        return [fieldName, value];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<
        T
    >;
}

const useForm = <T extends FieldMap>({form}: {form: FormLike<T>}) => {
    const initialState = useInitialState(form);
    const [values, setValues] = React.useState(initialState);

    const handlers = {
        "django.forms.widgets.CheckboxInput": (name: keyof T) => (value: boolean) => {
            setValues({
                ...values,
                [name]: value,
            });
        },
        "django.forms.widgets.TextInput": (name: keyof T) => (value: string) => {
            setValues({
                ...values,
                [name]: value,
            });
        },
    };
    const defaultHandler = (name: keyof T) => (value: string) => {
        setValues({
            ...values,
            [name]: value,
        });
    }

    type Tagged = {
        [K in Widget_GENERATEME["tag"]]: {
            name: Extract<keyof T, string>,
            tag: K;
            value: DiscriminateUnion<Widget_GENERATEME, "tag", K>["value_from_datadict"];
            handler: (value: DiscriminateUnion<Widget_GENERATEME, "tag", K>["value_from_datadict"]) => void;
            widget: DiscriminateUnion<Widget_GENERATEME, "tag", K>,
        };
    }[Widget_GENERATEME["tag"]];

    const iterate = (callback: (field: Tagged, thing: WidgetValues) => void) => {
        return form.iterator.map((fieldName) => {
            const field = form.fields[fieldName];
            const handler: any = (handlers[(field.widget as any).tag as keyof typeof handlers] ?? defaultHandler)(fieldName);

            return callback({
                name: fieldName,
                tag: (field.widget as any).tag,
                value: values[fieldName],
                handler,
                widget: field.widget as any,
            }, null as any)
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

export const Form = <T extends FieldMap>(props: {form: FormLike<T>}) => {
    const form = useForm(props);

    const rendered = form.iterate((field, thing) => {
        if (field.tag === "django.forms.widgets.CheckboxInput") {
            return <CheckboxInput key={field.name} name={field.name} value={field.value} onChange={field.handler} />
        }
        else if (field.tag === "django.forms.widgets.TextInput") {
            return (
                <TextInput
                    key={field.name}
                    name={field.name}
                    value={field.value}
                    onChange={field.handler}
                />
            );
        } else if (field.tag === "django.forms.widgets.SelectDateWidget") {

            return (
                <React.Fragment key={field.name}>
                    {field.widget.subwidgets.map((subwidget) => {
                        const unprefixedName = subwidget.name.replace(`${field.name}_`, "") as keyof typeof field.value;

                        return (
                            <Select
                                key={subwidget.name}
                                name={subwidget.name}
                                value={field.value[unprefixedName]}
                                optgroups={subwidget.optgroups}
                                onChange={(value) => {
                                    field.handler(
                                        {
                                            ...field.value,
                                            [unprefixedName]: value,
                                        }
                                    );
                                }}
                            />
                        );
                    })}
                </React.Fragment>
            );
        } else if (field.tag === "django.forms.widgets.Select") {
            return (
                <Select
                    key={field.name}
                    name={field.name}
                    value={field.value}
                    optgroups={field.widget.optgroups}
                    onChange={field.handler}
                />
            );
        }
    });

    return <div>
        {rendered}
        <h1>Form initial</h1>
        <pre>{JSON.stringify(form.initialState, null, 2)}</pre>
        <h1>Form state</h1>
        <pre>{JSON.stringify(form.values, null, 2)}</pre>
    </div>

}