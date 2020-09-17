import React from "react";
import {style} from "typestyle";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";
import {
    CSRFToken,
    Field,
    FieldMap,
    Fields,
    FormSetLike,
    ManagementForm,
} from "reactivated/forms";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

const FormSet = ({formSet}: {formSet: FormSetLike<FieldMap>}) => (
    <>
        <ManagementForm formSet={formSet} />
        <table>
            <thead>
                <tr>
                    <Fields form={formSet.empty_form}>
                        {({field}) => <th key={field.widget.name}>{field.label}</th>}
                    </Fields>
                </tr>
            </thead>
            <tbody>
                {formSet.forms.map((form) => (
                    <tr key={form.prefix}>
                        <Fields form={form}>
                            {({field, error}) => (
                                <td>
                                    <Field
                                        field={field}
                                        error={error}
                                        passed_validation={
                                            form.errors != null && error == null
                                        }
                                    />
                                </td>
                            )}
                        </Fields>
                    </tr>
                ))}
            </tbody>
        </table>
    </>
);

export default (props: Types["DataBrowserProps"]) => (
    <Layout title="Data browser">
        <form method="POST">
            <CSRFToken />
            <h1 className={styles.header}>Composers</h1>
            <Fields form={props.composer_form}>
                {({field, error}) => (
                    <Field
                        field={field}
                        error={error}
                        passed_validation={
                            props.composer_form.errors != null && error == null
                        }
                    />
                )}
            </Fields>
            <ManagementForm formSet={props.composer_form_set} />

            {props.composer_form_set.forms.map((formSetForm) => (
                <div key={formSetForm.prefix}>
                    <h2>{formSetForm.prefix}</h2>
                    <Fields form={formSetForm}>
                        {({field, error}) => (
                            <Field
                                field={field}
                                error={error}
                                passed_validation={
                                    formSetForm.errors != null && error == null
                                }
                            />
                        )}
                    </Fields>
                </div>
            ))}

            <h1 className={styles.header}>Operas</h1>
            <Fields form={props.opera_form}>
                {({field, error}) => (
                    <Field
                        field={field}
                        error={error}
                        passed_validation={
                            props.composer_form.errors != null && error == null
                        }
                    />
                )}
            </Fields>
            <ManagementForm formSet={props.opera_form_set} />
            <FormSet formSet={props.opera_form_set} />
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
