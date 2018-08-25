import React from 'react';

import {Widget, WidgetType} from './Widget';
import {Consumer} from '../context';


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

interface FieldMap {
    [name: string]: FieldLike;
}

interface FormLike<T extends FieldMap> {
    fields: T;
    errors: {[P in keyof T]: string[]|null};
    iterator: Array<keyof T>;
}

interface Props<U extends FieldMap> {
    className?: string;
    form: FormLike<U>|null;
    children?: React.ReactNode;
}

function iterate<T, U extends FieldMap>(form: FormLike<U>, callback: (field: FieldLike, error: string[]|null) => T) {
    return form.iterator.map((field_name) => callback(form.fields[field_name], form.errors[field_name]));
}

export const Form = <U extends FieldMap>(props: Props<U>) => {
    return <form method="POST" action="" className={props.className}>
        <Consumer>
            {context =>
            <input type="hidden" name="csrfmiddlewaretoken" value={context.csrf_token} />
            }
        </Consumer>
        {props.form != null &&
        <>
            {iterate(props.form, (field, error) =>
            <React.Fragment key={field.widget.name}>
                {'type' in field.widget && field.widget.type === 'hidden' ?
                <Widget widget={field.widget} />
                :
                <div>
                    <label>
                        <strong>{field.label}</strong>
                        <Widget widget={field.widget} />
                        {field.help_text !== '' &&
                        <small>{field.help_text}</small>
                        }
                    </label>
                    {error != null &&
                    <ul>
                        {error.map((error, index) =>
                        <li key={index}>{error}</li>
                        )}
                    </ul>
                    }
                </div>
                }
            </React.Fragment>
            )}
        </>
        }
        {props.children}
    </form>;
};
