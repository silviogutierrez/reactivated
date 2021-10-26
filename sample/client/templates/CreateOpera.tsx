import React from "react";

import {Layout} from "@client/components/Layout";
import {CSRFToken, Types} from "@client/generated";
import {useForm, FormLike, FieldMap} from "reactivated/forms";

const Form = <T extends FieldMap>(props: {form: FormLike<FieldMap>}) => {
    const form = useForm({form: props.form});
    return <div>
                {props.form.iterator.map((thing) => {
                    const field = props.form.fields[thing];

                    if (field.widget.subwidgets != null) {
                        return (
                            <div key={thing}>
                                <h1>{thing}</h1>
                                <div style={{display: "flex"}}>
                                {field.widget.subwidgets.map((subwidget) => (
                                    <input
                                        key={subwidget.name}
                                        type="text"
                                        name={subwidget.name}
                                        onChange={(event) => {
                                            const unprefixed = subwidget.name.replace(`${field.widget.name}_`, "");

                                            const value = {
                                                ...form.values[thing] as any,
                                                [unprefixed]: event.target.value,
                                            }
                                            form.handleChange(thing, value);
                                        }}
                                    />
                                ))}
                                </div>
                            </div>
                        );
                    }

                    return (
                        <div key={thing}>
                            <h1>{thing}</h1>
                            <input
                                type="text"
                                name={field.widget.name}
                                value={form.values[thing] ?? "" as any}
                                onChange={(event) =>
                                    form.handleChange(thing, event.target.value)
                                }
                            />
                        </div>
                    );
                })}
                <button type="submit">Submit</button>
                <div>
                <h1>Form</h1>
                <pre>{JSON.stringify(form.values, null, 2)}</pre>
                <pre>{JSON.stringify(form.initialState, null, 2)}</pre>
                </div>
                <div></div>
        </div>
}


export default (props: Types["CreateOperaProps"]) => {
    return (
        <Layout title="Create opera">
            <form method="POST" action="">
                <CSRFToken />
                <div style={{display: "flex"}}>
                    <Form form={props.form} />
                    <Form form={props.pre_filled} />
                    <Form form={props.posted} />
                </div>
                {/*
            <Form form={this.props.form}>
                <button type="submit">Submit</button>
            </Form>
        */}
            </form>
        </Layout>
    );
};
