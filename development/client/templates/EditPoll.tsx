import React from "react";

import {CSRFToken, Iterator, ManagementForm, templates, useFormSet} from "@reactivated";

import {Layout} from "@client/components/Layout";
import * as forms from "@client/forms";

export const Template = (props: server.example.templates.EditPoll) => {
    const formSet = forms.useFormSet({formSet: props.choice_form_set});
    const title = props.existing_poll == null ? "Create poll" : "Update poll";

    return (
        <Layout title={title} className="flex flex-col gap-2.5">
            <h1>{title}</h1>
            <form method="POST" action="" className="flex flex-col gap-2.5">
                <forms.CSRFToken />
                <forms.Fieldset>
                    <forms.Iterator form={props.form}>
                        {(field) => <forms.Field field={field} />}
                    </forms.Iterator>
                </forms.Fieldset>
                <forms.ManagementForm formSet={formSet.schema} />

                {formSet.forms.map((form) => (
                    <forms.Fieldset key={form.form.prefix} className="flex gap-2.5">
                        <forms.Iterator form={form}>
                            {(field) => <forms.Field field={field} />}
                        </forms.Iterator>
                    </forms.Fieldset>
                ))}
                <div className="flex gap-2.5">
                    <forms.Button type="submit">Submit</forms.Button>
                    <forms.Button type="button" onClick={formSet.addForm}>
                        Add another choice
                    </forms.Button>
                </div>
            </form>
        </Layout>
    );
};
