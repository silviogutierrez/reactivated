import React from "react";

import {CSRFToken, Iterator, templates} from "@reactivated";

import {css, cx} from "@linaria/core";

import {ManagementForm, useFormSet} from "reactivated/forms";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import * as styles from "@client/styles";

export default (props: templates.EditPoll) => {
    const formSet = useFormSet({formSet: props.choice_form_set});
    const title = props.existing_poll == null ? "Create poll" : "Update poll";

    return (
        <Layout
            title={title}
            className={css`
                ${styles.verticallySpaced(10)}
            `}
        >
            <h1>{title}</h1>
            <form
                method="POST"
                action=""
                className={css`
                    ${styles.verticallySpaced(10)}
                `}
            >
                <CSRFToken />
                <forms.Fieldset>
                    <Iterator form={props.form}>
                        {(field) => <forms.Field field={field} />}
                    </Iterator>
                </forms.Fieldset>
                <ManagementForm formSet={formSet.schema} />

                {formSet.forms.map((form) => (
                    <forms.Fieldset
                        key={form.form.prefix}
                        className={cx(
                            styles.horizontallySpaced,
                            css`
                                display: flex;
                                & > * {
                                    flex: 1;
                                }
                            `,
                        )}
                    >
                        <Iterator form={form}>
                            {(field) => <forms.Field field={field} />}
                        </Iterator>
                    </forms.Fieldset>
                ))}
                <div className={styles.horizontallySpaced}>
                    <forms.Button type="submit">Submit</forms.Button>
                    <forms.Button type="button" onClick={formSet.addForm}>
                        Add another choice
                    </forms.Button>
                </div>
            </form>
        </Layout>
    );
};
