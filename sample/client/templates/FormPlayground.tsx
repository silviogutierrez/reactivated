import React from "react";

// import {Form} from "reactivated";

import {Types} from "@client/generated";

export default (props: Types["FormPlaygroundProps"]) => {
    return (
        <div>
            {props.form.iterator.map((thing) => (
                <h1 key={thing}>{thing}</h1>
            ))}
            {/*
            <Form form={this.props.form}>
                <button type="submit">Submit</button>
            </Form>
        */}
        </div>
    );
};
