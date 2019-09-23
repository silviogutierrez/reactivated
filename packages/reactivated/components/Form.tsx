import React from 'react';

import {style} from 'typestyle';
import {Widget, WidgetType, getValueForSelect} from './Widget';
import {Field} from './Field';
import {Consumer} from '../context';

import { Alert, Button, FormGroup, Label, Input, FormText, FormFeedback } from 'reactstrap';

type TODO = any;

export const Styles = {
    // Bootstrap hides error messages unless they are general siblings of
    // a form-control. This isn't the case with the autocomplete and other
    // composite widgets. So we force it to always display.
    feedback: style({
        display: 'block',
    }),
} as const;


interface FieldLike {
    widget: WidgetType;
    label: string;
    help_text: string;
};

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

export interface FieldMap {
    [name: string]: FieldLike;
}

export interface FormLike<T extends FieldMap> {
    fields: T;
    errors: {[P in keyof T]?: string[]}|null;
    iterator: Array<keyof T>;
    prefix: string;
}

interface Props<U extends FieldMap> {
    className?: string;
    form: FormLike<U>|null;
    children?: React.ReactNode;
    onChange?: (name: string, value: any) => {};
    getFields?: (form: FormLike<U>, state: any) => Array<keyof U>;
}

export function iterate<T, U extends FieldMap>(form: FormLike<U>, callback: (field: FieldLike, error: string[]|null|undefined) => T) {
    return form.iterator.map((field_name) => callback(form.fields[field_name], form.errors != null ? form.errors[field_name] :  null));
}

export const Form2 = <U extends FieldMap>(props: Props<U>) => {
};

export class Form<U extends FieldMap> extends React.Component<Props<U>> {
    getFields<T>(filter: boolean, callback: (field: FieldLike, error: string[]|null|undefined) => T) {
        const {form} = this.props;

        if (form == null) {
            return [];
        }

        const filteredIterator = filter === true && this.props.getFields != null ? this.props.getFields(form, this.state) : form.iterator;

        return filteredIterator.map((field_name) => callback(form.fields[field_name], form.errors != null ? form.errors[field_name] :  null));
    }

    constructor(props: Props<U>) {
        super(props)
        let state: any = {};

        if (props.form != null) {
            this.getFields(false, (field, error) => {
                const widget = field.widget;

                if (widget.template_name == "django/forms/widgets/select.html") {
                    state[field.widget.name] = getValueForSelect(widget);
                }
                else {
                    state[field.widget.name] = widget.value;
                }
            });
        }

        this.state = state;
    }

    handleOnChange = (event: React.FormEvent<HTMLFormElement>) => {
        const target = event.target as TODO;
        this.setState({
            [target.name]: target.value,
        })
    }

    render() {
        const {props} = this;

        return <form method="POST" action="" className={props.className} onChange={this.handleOnChange} encType="multipart/form-data">
            <Consumer>
                {context =>
                <input type="hidden" name="csrfmiddlewaretoken" value={context.csrf_token} />
                }
            </Consumer>
            {props.form != null &&
            <>
                {props.form.errors != null && props.form.errors.__all__ != null &&
                <>
                    {props.form.errors.__all__.map((error, index) =>
                    <Alert key={index} color="danger" fade={false}>
                        {error}
                    </Alert>
                    )}
                </>
                }
                {this.getFields(true, (field, error) =>
                <Field key={field.widget.name} field={field} error={error || null} passed_validation={props.form!.errors != null && error == null} />
                )}
            </>
            }
            {props.children}
        </form>;
    }
}
