import React from "react";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";

export default class extends React.Component<Types["FormPlaygroundProps"], {}> {
    render() {
        return (
            <Layout title="Form playground">
                {/*
                <Form form={this.props.form}>
                    <button type="submit">Submit</button>
                </Form>
                */}
            </Layout>
        );
    }
}
