import React from "react";

import {Types, Iterator, CSRFToken} from "@client/generated";
import {Layout} from "@client/components/Layout";

import {Widget} from "reactivated/forms";


export default (props: Types["CreateQuestionProps"]) => (
    <Layout title="Create question">
        <form method="POST" action="">
            <CSRFToken />
            <Iterator form={props.form}>
                {(field) =>
                    <Widget field={field} />
                }
            </Iterator>
            <button type="submit">Submit</button>
        </form>
    </Layout>
);
