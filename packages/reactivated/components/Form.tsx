import React from 'react';

import {Widget, WidgetType} from './Widget';
import {Consumer} from '../context';


interface FieldLike {
    widget: WidgetType;
    label: string;
};

interface Form {
    fields: {
        [name: string]: FieldLike;
    },
    errors: {
        [P in keyof this['fields']]: string[]|null;
    }
    iterator: Array<keyof this['fields']>;
}

interface Props {
    className?: string;
    form: Form|null;
    children?: React.ReactNode;
}

function iterate<T>(form: Form, callback: (field: FieldLike, error: string[]|null) => T) {
    return form.iterator.map((field_name) => callback(form.fields[field_name], form.errors[field_name]));
}

export const Form = (props: Props) => {
    return <form method="POST" action="" className={props.className}>
        <Consumer>
            {context =>
            <input type="hidden" name="csrfmiddlewaretoken" value={context.csrf_token} />
            }
        </Consumer>
        {props.form != null &&
        <>
            {iterate(props.form, (field, error) =>
            <div key={field.widget.name}>
                <label>
                    {field.label}
                    <Widget widget={field.widget} />
                </label>
                {error != null &&
                <ul>
                    {error.map((error, index) =>
                    <li key={index}>{error}</li>
                    )}
                </ul>
                }
            </div>
            )}
        </>
        }
        {props.children}
    </form>;
};
