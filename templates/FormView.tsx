import React from 'react';

import {Layout} from '../components/Layout';
import {Form} from '../components/Form';
import {FormViewProps} from '../models';
import {WidgetType as Foo} from '../components/Widget';

interface Widget {
    name: string;
    url: string;
}


interface Props extends FormViewProps {
    // form: FormType;
    // widget_list: Widget[];
    csrf_token: string;
}

export default (props: Props) => <Layout>
    <ul>
        {props.widget_list.map(widget =>
        <li key={widget.name}>{widget.name}</li>
        )}
    </ul>
    <Form csrf_token={props.csrf_token} form={props.form} />
</Layout>;
