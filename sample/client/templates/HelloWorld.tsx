import React from "react";

import {Types} from "@client/generated";
import {Layout} from "@client/Layout";

export default (props: Types["HelloWorldProps"]) => {
    const [showStyle, setShowStyle] = React.useState(false);

    return (
        <Layout title="Hello world!">
            <h1>Hello World!</h1>
            <p>
                The best opera is <strong>{props.opera.name}</strong> by{" "}
                <strong>{props.opera.composer.name}</strong>.
            </p>
            {showStyle === false ? (
                <p>
                    Click{" "}
                    <a href="#" onClick={() => setShowStyle(true)}>
                        here
                    </a>{" "}
                    to see what style of opera it is.
                </p>
            ) : (
                <p>
                    <strong>Style:</strong> {props.opera.style}
                </p>
            )}
        </Layout>
    );
};
