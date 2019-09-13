import React from "react";
import {style} from "typestyle";

import {Form, FormSet} from "reactivated";

import {TypedTemplate} from "@client/generated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default class extends TypedTemplate {
    render() {
        return <div className={styles.layout}>
            <h1>Hello</h1>
        </div>
    }
}
