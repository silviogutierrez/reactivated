import React from 'react';

import * as models from '../../models';
import {Widget, WidgetType} from './Widget';

interface Form {
    fields: {
        [name: string]: models.FieldType;
    },
    errors: {
        [P in keyof this['fields']]: string[]|null;
    }
    iterator: Array<keyof this['fields']>;
}

interface Props {
    csrf_token: string;
    form: Form;
    children?: React.ReactNode;
}

function iterate<T>(form: Form, callback: (field: models.FieldType, error: string[]|null) => T) {
    return form.iterator.map((field_name) => callback(form.fields[field_name], form.errors[field_name]));
}

export const Form = (props: Props) => {
    return <form method="POST" action="">
        <input type="hidden" name="csrfmiddlewaretoken" value={props.csrf_token} />
        {/*Object.keys(props.form.errors).length > 0 &&
        <pre>{JSON.stringify(props.form.errors, null, 2)}</pre>
        */}
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
        {props.children}
    </form>;
};
