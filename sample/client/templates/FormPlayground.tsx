import React from "react";
import {style} from "typestyle";

import {Form, FormSet} from "reactivated";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";

export default class extends React.Component<Types["FormPlaygroundProps"], {}> {
    render() {
        return (
            <Layout>
                <Form form={this.props.form}>
                    <button type="submit">Submit</button>
                </Form>
            </Layout>
        );
    }
}
