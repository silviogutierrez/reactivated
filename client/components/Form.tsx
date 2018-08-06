import React from 'react';

import {FormType} from '../../models';
import {Widget, WidgetType} from './Widget';

/*
 * Manually-typed.
interface Field {
    name: string;
    label: string;
    widget: WidgetType;
}

type FormError = string[];

export type FormType = {
    errors: {
        [name: string]: FormError|null;
    };
    fields: Field[];
}
*/

interface Props {
    csrf_token: string;
    form: FormType;
    children?: React.ReactNode;
}

export const Form = (props: Props) => {
    return <form method="POST" action="">
        <input type="hidden" name="csrfmiddlewaretoken" value={props.csrf_token} />
        {/*Object.keys(props.form.errors).length > 0 &&
        <pre>{JSON.stringify(props.form.errors, null, 2)}</pre>
        */}
        {props.form.fields.map(field =>
        <div key={field.widget.name}>
            <label>
                {field.label}
                <Widget widget={field.widget} />
            </label>
            {props.form.errors[field.name] != null &&
            <ul>
                {props.form.errors[field.name]!.map((error, index) =>
                <li key={index}>{error}</li>
                )}
            </ul>
            }
        </div>
        )}
        {props.children}
    </form>;
};
