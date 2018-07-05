import React from 'react';

import {FormType, Form} from '../components/Form';

interface Props {
    form: FormType;
}

export default (props: Props) => <Form form={props.form} />;
