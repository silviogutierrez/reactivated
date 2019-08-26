import React from "react";

import {Form, FormLike, iterate} from "./Form";
import {Widget} from "./Widget";

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
    prefix: string;
}

interface Props {
    formSet: FormSetType;
    children?: React.ReactNode;
}

export const FormSet = ({formSet, children}: Props) => (
    <Form form={null}>
        <input
            type="hidden"
            name={`${formSet.prefix}-INITIAL_FORMS`}
            value={formSet.initial}
        />
        <input
            type="hidden"
            name={`${formSet.prefix}-TOTAL_FORMS`}
            value={formSet.total}
        />

        {iterate(formSet.management_form, field => (
            <th key={field.widget.name}>{field.label}</th>
        ))}
        <table>
            <thead>
                <tr>
                    {iterate(formSet.empty_form, field => (
                        <th key={field.widget.name}>{field.label}</th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {formSet.forms.map(form => (
                    <tr key={form.prefix}>
                        {iterate(form, (field, error) => (
                            <td key={field.widget.name}>
                                <Widget
                                    widget={field.widget}
                                    has_errors={error != null}
                                    passed_validation={
                                        form.errors != null && error == null
                                    }
                                />
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
        {children}
    </Form>
);
