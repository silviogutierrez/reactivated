import React from 'react';

import {FormType, Form} from '../components/Form';

interface Props {
    form: FormType;
    widget_list: string[];
    csrf_token: string;
}

export default (props: Props) => <div>
    <ul>
        {props.widget_list.map(widget =>
        <li key={widget}>{widget}</li>
        )}
    </ul>
    <Form csrf_token={props.csrf_token} form={props.form} />
</div>;
