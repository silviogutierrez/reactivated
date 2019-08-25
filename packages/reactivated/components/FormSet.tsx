import React from 'react';

import {Form, FormLike} from './Form';

interface FormSetType {
  initial: number;
  total: number;
  max_num: number;
  min_num: number;
  can_delete: boolean;
  can_order: boolean;

  forms: Array<FormLike<any>>;
  empty_form: FormLike<any>;
  management_form: FormLike<any>;
}

interface Props {
  formSet: FormSetType;
  children?: React.ReactNode;
}

export const FormSet = (props: Props) => <div>
    {props.formSet.forms.map((form, index) =>
    <Form key={index} form={form}>
    </Form>
    )}
    {props.children}
</div>;
