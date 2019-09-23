import React from "react";

import {Widget, WidgetType, getValueForSelect} from "./Widget";
import {FieldMap, FormLike} from "./Form";
import {Field} from "./Field";
import {Consumer} from "../context";

import {Alert, Button, FormGroup, Label, Input, FormText, FormFeedback} from "reactstrap";

type TODO = any;

interface FieldLike {
    widget: WidgetType;
    label: string;
    help_text: string;
}

/*
interface Form {
    fields: {
        [name: string]: FieldLike;
    },
    errors: {
        [P in keyof this['fields']]: string[]|null;
    }
    iterator: Array<keyof this['fields']>;
}
*/

interface Props<U extends FieldMap> {
    className?: string;
    form: FormLike<U> & {sections: Array<{label: string; fields: Array<keyof U>}>};
    children?: React.ReactNode;
    filterFields?: (
        form: FormLike<U>,
        fields: Array<keyof U>,
        state: any,
    ) => Array<keyof U>;
}

function iterate<T, U extends FieldMap>(
    form: FormLike<U>,
    fields: Array<keyof U>,
    callback: (field: FieldLike, error: string[] | null | undefined) => T,
) {
    return fields.map(field_name =>
        callback(
            form.fields[field_name],
            form.errors != null ? form.errors[field_name] : null,
        ),
    );
}

export class SectionalForm<U extends FieldMap> extends React.Component<Props<U>> {
    constructor(props: Props<U>) {
        super(props);
        let state: any = {};

        iterate(props.form, props.form.iterator, field => {
            if (field.widget.template_name == "django/forms/widgets/select.html") {
                state[field.widget.name] = getValueForSelect(field.widget);
            } else {
                state[field.widget.name] = field.widget.value;
            }
        });

        this.state = state;
    }

    filterFields(fields: Array<keyof U>) {
        return this.props.filterFields != null
            ? this.props.filterFields(this.props.form, fields, this.state)
            : fields;
    }

    handleOnChange = (event: React.FormEvent<HTMLFormElement>) => {
        const target = event.target as TODO;
        this.setState({
            [target.name]: target.value,
        });
    };

    render() {
        const {props} = this;

        return (
            <form
                method="POST"
                action=""
                className={props.className}
                onChange={this.handleOnChange}
                encType="multipart/form-data"
            >
                <Consumer>
                    {context => (
                        <input
                            type="hidden"
                            name="csrfmiddlewaretoken"
                            value={context.csrf_token}
                        />
                    )}
                </Consumer>

                {props.form.errors != null && props.form.errors.__all__ != null &&
                <>
                    {props.form.errors.__all__.map((error, index) =>
                    <Alert key={index} color="danger" fade={false}>
                        {error}
                    </Alert>
                    )}
                </>
                }

                {props.form.sections.map((section, index) => (
                    <fieldset key={index}>
                        <h2>{section.label}</h2>
                        {iterate(
                            props.form,
                            this.filterFields(section.fields),
                            (field, error) => (
                            <Field key={field.widget.name} field={field} error={error || null} passed_validation={props.form!.errors != null && error == null} />
                            ),
                        )}
                    </fieldset>
                ))}
                {props.children}
            </form>
        );
    }
}
