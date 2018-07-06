import React from 'react';

import {Widget, WidgetType} from './Widget';

interface Field {
    widget: WidgetType;
}

type FormError = string[];

export type FormType = {
    errors: {
        [name: string]: FormError;
    };
    fields: Field[];
}

interface Props {
    csrf_token: string;
    form: FormType;
}

export const Form = (props: Props) => {
    return <form method="POST" action="">
        <input type="hidden" name="csrfmiddlewaretoken" value={props.csrf_token} />
        {Object.keys(props.form.errors).length > 0 &&
        <pre>{JSON.stringify(props.form.errors, null, 2)}</pre>
        }
        {props.form.fields.map(field =>
        <div key={field.widget.name}>
            <Widget widget={field.widget} />
        </div>
        )}
        <button type="submit">Submit</button>
    </form>;
};
