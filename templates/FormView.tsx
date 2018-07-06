import React from 'react';

import {FormType, Form} from '../components/Form';

interface Props {
    form: FormType;
    csrf_token: string;
}

export default (props: Props) => <Form csrf_token={props.csrf_token} form={props.form} />;
