import React, { useDebugValue } from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types} from "@client/generated";
import {useForm, FormLike, FormHandler, FieldMap} from "reactivated/forms";

import {
    ReactivatedSerializationCheckboxInput,
    ReactivatedSerializationSelectDateWidget,
    ReactivatedSerializationSelect,
    ReactivatedSerializationTextInput,
} from "@client/generated";

type WidgetType =
    | ReactivatedSerializationCheckboxInput
    | ReactivatedSerializationSelectDateWidget
    | ReactivatedSerializationSelect
    | ReactivatedSerializationTextInput;

type DiscriminateUnion<T, K extends keyof T, V extends T[K]> = T extends Record<K, V>
? T
: never;


type GetValue<T> = T extends {value_from_datadict: unknown} ? T["value_from_datadict"] : string;


type Validators = {[K in WidgetType["tag"]]: (widget: DiscriminateUnion<WidgetType, "tag", K>, value: unknown) => GetValue<DiscriminateUnion<WidgetType, "tag", K>>};

const validators: Validators = {
    "django.forms.widgets.CheckboxInput": (widget, value) => {
        if (widget.attrs.checked === true) {
            return true;
        }
        return false;
    },
    "django.forms.widgets.SelectDateWidget": (value) => {
        return "selectdate";
    },
    "django.forms.widgets.Select": (widget, value) => {
        return widget.value[0];
    },
    "django.forms.widgets.TextInput": (widget) => {
        return widget.value ?? "";
    },
};

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

const TextInput = (props: {name: string, value: string, onChange: (value: string) => void}) => {
    return (
        <input
            type="text"
            name={props.name}
            value={props.value}
            onChange={(event) => props.onChange(event.target.value)}
        />
    );
}

const Widget = ({form, widget}: {form: FormHandler<any>; widget: WidgetType}) => {
    if (widget.tag === "django.forms.widgets.TextInput") {
        return (
            <input
                type="text"
                name={widget.name}
                value={form.values[widget.name] ?? ("" as any)}
                onChange={(event) => form.handleChange(widget.name, event.target.value)}
            />
        );
    } else if (widget.tag === "django.forms.widgets.CheckboxInput") {
        return (
            <input
                type="checkbox"
                name={widget.name}
                checked={form.values[widget.name] ?? false}
                onChange={(event) =>
                    form.handleChange(widget.name, event.target.checked)
                }
            />
        );
    } else if (widget.tag === "django.forms.widgets.Select") {
        const selected = Array.isArray(form.values[widget.name])
            ? form.values[widget.name][0]
            : form.values[widget.name];

        return (
            <select
                value={selected ?? ""}
                onChange={(event) => {
                    form.handleChange(widget.name, event.target.value);
                }}
            >
                {widget.optgroups.map((optgroup) => {
                    const member = optgroup[1][0];
                    const value = member.value == null ? "" : member.value.toString();
                    return (
                        <option key={value} value={value}>
                            {member.label}
                        </option>
                    );
                })}
            </select>
        );
    }

    return <div>TODO</div>;
};

type FormValue<U> = U extends {value_from_datadict: unknown} ? U["value_from_datadict"] : U extends {subwidgets: unknown}
    ? {subwidget: "TBD"}
    : U extends ReactivatedSerializationSelect ? U["optgroups"][number][1][0]["value"] : "";


export type FormValues<U extends FieldMap> = Simplify<{
    [K in keyof U]: FormValue<U[K]["widget"]>;
}>;

const useInitialState = <T extends FieldMap>(form: FormLike<T>) => {
    const initialValuesAsEntries = form.iterator.map((fieldName) => {
        // const field = fieldInterceptor(form, fieldName);
        const field = form.fields[fieldName];
        const widget = field.widget as WidgetType;

        const value = widget.tag in validators ? validators[widget.tag](widget as any, widget.value) : widget.value;
        return [fieldName, value];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<
        T
    >;
}


const useNewForm = <T extends FieldMap>({form}: {form: FormLike<T>}) => {
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

    type Tagged = {[K in keyof T]: {
        name: K,
        tag: T[K]["widget"] extends WidgetType ? T[K]["widget"]["tag"] : never,
        value: T[K]["widget"] extends {"value_from_datadict": unknown} ? T[K]["widget"]["value_from_datadict"] : string,
        handler: T[K]["widget"] extends {"value_from_datadict": unknown} ? (value: T[K]["widget"]["value_from_datadict"]) => void : (value: string) => void,
        widget: T[K]["widget"],
    }};

    const iterate = (callback: (field: Tagged[keyof T]) => void) => {
        return form.iterator.map((fieldName) => {
            const field = form.fields[fieldName];
            const handler: any = (handlers[(field.widget as any).tag as keyof typeof handlers] ?? defaultHandler)(fieldName);

            return callback({
                name: fieldName,
                tag: (field.widget as any).tag,
                value: values[fieldName],
                handler,
                widget: field.widget,
            })
        });
    }


    return {values, initialState, setValues, iterate};
}

const Form = <T extends FieldMap>(props: {form: FormLike<FieldMap>}) => {
    const form = useNewForm({form: props.form});
    
    return (
        <div>
            {props.form.iterator.map((thing) => {
                const field = props.form.fields[thing];

                /*
                if (field.widget.subwidgets != null) {
                    return (
                        <div key={thing}>
                            <h1>{thing}</h1>
                            <div style={{display: "flex"}}>
                                {field.widget.subwidgets.map((subwidget) => (
                                    <input
                                        key={subwidget.name}
                                        type="text"
                                        name={subwidget.name}
                                        onChange={(event) => {
                                            const unprefixed = subwidget.name.replace(
                                                `${field.widget.name}_`,
                                                "",
                                            );

                                            const value = {
                                                ...(form.values[thing] as any),
                                                [unprefixed]: event.target.value,
                                            };
                                            form.handleChange(thing, value);
                                        }}
                                    />
                                ))}
                            </div>
                        </div>
                    );
                }
                */

                const widget = (field.widget as WidgetType);
                return (
                    <div key={thing}>
                        <h1>{thing}</h1>
                        {widget.tag === "django.forms.widgets.CheckboxInput" && (
                            <CheckboxInput
                                name={field.widget.name}
                                value={(form.values[thing as any] as any) as boolean}
                                onChange={(value) => {
                                    form.setValues({...form.values, [thing]: value as any});
                                    console.log("ok");
                                }}
                            />
                        )}
                        {widget.tag === "django.forms.widgets.TextInput" && (
                            <TextInput
                                name={field.widget.name}
                                value={form.values[thing]}
                                onChange={(value) => {
                                    form.setValues({...form.values, [thing]: value as any});
                                }}
                            />
                        )}
                        {/*
                        <Widget form={form} widget={field.widget as WidgetType} />
                        */}
                        {/*}
                        <input
                            type="text"
                            name={field.widget.name}
                            value={form.values[thing] ?? ("" as any)}
                            onChange={(event) =>
                                form.handleChange(thing, event.target.value)
                            }
                        />
                        */}
                    </div>
                );
            })}
            <button type="submit">Submit</button>
            <div>
                <h1>Form initial</h1>
                <pre>{JSON.stringify(form.initialState, null, 2)}</pre>
                <h1>Form state</h1>
                <pre>{JSON.stringify(form.values, null, 2)}</pre>
            </div>
            <div></div>
        </div>
    );
};

type Simplify<T> = {[KeyType in keyof T]: T[KeyType]};

export default (props: Types["CreateOperaProps"]) => {
    const preFilled = useNewForm({form: props.pre_filled});
    const rendered = preFilled.iterate(field => {
        if (field.tag === "django.forms.widgets.CheckboxInput") {
            return <CheckboxInput key={field.name} name={field.name} value={field.value} onChange={field.handler} />
        }
        else if (field.tag === "django.forms.widgets.TextInput") {
            return <TextInput key={field.name} name={field.name} value={field.value} onChange={field.handler} />
        }
    });
    const casted = useInitialState(props.pre_filled);
    /*
    initialState = {

    }
    */

    return (
        <Layout title="Create opera">
            {rendered}
            <h1>Form initial</h1>
            <pre>{JSON.stringify(preFilled.initialState, null, 2)}</pre>
            <h1>Form state</h1>
            <pre>{JSON.stringify(preFilled.values, null, 2)}</pre>
            <form method="POST" action="">
                <CSRFToken />
                <div style={{display: "flex"}}>
                    <Form form={props.form} />
                    <Form form={props.pre_filled} />
                    <Form form={props.posted} />
                </div>
                {/*
            <Form form={this.props.form}>
                <button type="submit">Submit</button>
            </Form>
        */}
            </form>
        </Layout>
    );
};
