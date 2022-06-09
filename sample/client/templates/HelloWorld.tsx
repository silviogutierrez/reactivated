import React from "react";

import {templates} from "@reactivated";
import {Layout} from "@client/Layout";
import {css} from "@linaria/core";
import {styled} from "@linaria/react";

const Paragraph = styled.p`
    color: #444;
`;

export default (props: templates.HelloWorld) => {
    const [showStyle, setShowStyle] = React.useState(false);

    return (
        <Layout title="Hello world!">
            <h1
                className={css`
                    color: blue;
                `}
            >
                Hello World!
            </h1>
            <Paragraph>
                The best opera is <strong>{props.opera.name}</strong> by{" "}
                <strong>{props.opera.composer.name}</strong>.
            </Paragraph>
            {showStyle === false ? (
                <Paragraph>
                    Click{" "}
                    <a href="#" onClick={() => setShowStyle(true)}>
                        here
                    </a>{" "}
                    to see what style of opera it is.
                </Paragraph>
            ) : (
                <Paragraph>
                    <strong>Style:</strong> {props.opera.style}
                </Paragraph>
            )}
        </Layout>
    );
};
