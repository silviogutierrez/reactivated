import React from "react";

import {css} from "@linaria/core";

import {ManagementForm, useFormSet} from "reactivated/forms";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";
import {CSRFToken, Iterator, Types} from "@client/generated";
import * as styles from "@client/styles";

export default (props: Types["CreatePollProps"]) => {
    const formSet = useFormSet({formSet: props.choice_form_set});

    return (
        <Layout title="Create question">
            <h1>Update poll</h1>
            <form method="POST" action="" className={styles.verticallySpaced}>
                <CSRFToken />
                <Iterator form={props.form}>
                    {(field) => <forms.Field field={field} />}
                </Iterator>
                <ManagementForm formSet={formSet.schema} />

                {formSet.handlers.map((handler) => (
                    <div
                        key={handler.form.prefix}
                        className={css`
                            display: flex;
                            & > * {
                                flex: 1;
                            }
                        `}
                    >
                        <Iterator form={handler}>
                            {(field) => <forms.Field field={field} />}
                        </Iterator>
                    </div>
                ))}
                <div className={styles.horizontallySpaced}>
                    <button type="submit">Submit</button>
                    <button type="button" onClick={formSet.addForm}>
                        Add another choice
                    </button>
                </div>
            </form>
        </Layout>
    );
};
