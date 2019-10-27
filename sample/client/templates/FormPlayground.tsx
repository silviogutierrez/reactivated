import React from "react";
import {style} from "typestyle";

import {Form, FormSet} from "reactivated";

import {Layout} from "@client/components/Layout";
import {FormPlayground} from "@client/generated";

export default class extends FormPlayground {
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
