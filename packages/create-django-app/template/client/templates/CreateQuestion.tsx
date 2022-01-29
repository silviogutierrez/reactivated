import React from "react";

import {Types, Iterator, CSRFToken} from "@client/generated";
import {Layout} from "@client/components/Layout";

import {Widget} from "reactivated/forms";

export default (props: Types["CreateQuestionProps"]) => (
    <Layout title="Create question">
        <h1>Create poll</h1>
        <form method="POST" action="">
            <CSRFToken />
            <Iterator form={props.form}>
                {(field) => (
                    <div>
                        <h2>{field.label}</h2>
                        <Widget field={field} />
                    </div>
                )}
            </Iterator>
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
