import React from "react";

import {Types} from "@client/generated";
import {Layout} from "@client/Layout";

import {useForm} from "reactivated/forms/genesis";

const SPACING = 2;

export default (props: Types["StoryboardProps"]) => {
    const handler = useForm({form: props.form});

    return (
        <Layout title="Storyboard">
            <h1>Storyboard</h1>
            <pre>{JSON.stringify(props.form, null, SPACING)}</pre>
        </Layout>
    );
};
