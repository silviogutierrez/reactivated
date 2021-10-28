import React from "react";

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


type GetValue<T> = T extends {value_from_datadict: unknown} ? T["value_from_datadict"] : string | null;


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
        return widget.value;
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

    return {values, initialState, setValues};
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
                <h1>Form</h1>
                <pre>{JSON.stringify(form.values, null, 2)}</pre>
                <pre>{JSON.stringify(form.initialState, null, 2)}</pre>
            </div>
            <div></div>
        </div>
    );
};

type Simplify<T> = {[KeyType in keyof T]: T[KeyType]};

export default (props: Types["CreateOperaProps"]) => {
    const casted = useInitialState(props.pre_filled);
    /*
    initialState = {

    }
    */

    return (
        <Layout title="Create opera">
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
