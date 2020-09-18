import React from "react";
import {Alert, FormFeedback} from "reactstrap";
import {classes, style} from "typestyle";

import {Form, FormLike, iterate, Styles} from "./Form";
import {isHidden, Widget} from "./Widget";

const styles = {
    hidden: style({display: "none"}),
} as const;

interface FormSetType {
    initial: number;
    total: number;
    max_num: number;
    min_num: number;
    can_delete: boolean;
    can_order: boolean;
    non_form_errors: string[];

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

        {formSet.non_form_errors.map((error, index) => (
            <Alert key={index} color="danger" fade={false}>
                {error}
            </Alert>
        ))}

        <table>
            <thead>
                <tr>
                    {iterate(formSet.empty_form, (field) => (
                        <th
                            key={field.widget.name}
                            className={classes(isHidden(field.widget) && styles.hidden)}
                        >
                            {field.label}
                        </th>
                    ))}
                </tr>
            </thead>
            <tbody>
                {formSet.forms.map((form) => (
                    <tr key={form.prefix}>
                        {iterate(form, (field, error) => (
                            <td
                                key={field.widget.name}
                                className={classes(
                                    isHidden(field.widget) && styles.hidden,
                                )}
                            >
                                <Widget
                                    widget={field.widget}
                                    has_errors={error != null}
                                    passed_validation={
                                        form.errors != null && error == null
                                    }
                                />

                                {error != null && (
                                    <FormFeedback className={Styles.feedback}>
                                        {error.map((errorMessage, index) => (
                                            <div key={index}>{errorMessage}</div>
                                        ))}
                                    </FormFeedback>
                                )}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
        {children}
    </Form>
);
