import React from "react";
import {style} from "typestyle";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types} from "@client/generated";
import {FieldMap, Fields, FormSetLike, ManagementForm} from "reactivated/forms";

const Field = (props: any) => {
    return <div>TODO</div>;
};

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
                                        label={false}
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
            <ManagementForm formSet={props.composer_form_set} />

            {props.composer_form_set.forms.map((formSetForm) => (
                <div key={formSetForm.prefix}>
                    <h3>Composer: {formSetForm.fields.name.widget.value}</h3>
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
            <h3>Add new</h3>
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

            <h1 className={styles.header}>Operas</h1>
            <ManagementForm formSet={props.opera_form_set} />
            <FormSet formSet={props.opera_form_set} />
            <h3>Add opera</h3>
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
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
