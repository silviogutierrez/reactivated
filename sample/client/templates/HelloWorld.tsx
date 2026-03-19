import React from "react";

import {Layout} from "@client/Layout";
import {templates} from "@reactivated";

const Paragraph = (props: {children?: React.ReactNode}) => (
    <p className="text-[#444]">{props.children}</p>
);

export const Template = (props: templates.HelloWorld) => {
    const [showStyle, setShowStyle] = React.useState(false);

    return (
        <Layout title="Hello world!">
            <div>
                <h1>Hello World! It's good to be here.</h1>
            </div>
            <Paragraph>
                The <span className="text-yellow-400">best</span> opera is{" "}
                <strong>{props.opera.name}</strong> by{" "}
                <strong>{props.opera.composer.name}</strong>.
            </Paragraph>
            {showStyle === false ? (
                <Paragraph>
                    Click{" "}
                    <a href="#" onClick={() => setShowStyle(true)}>
                        here
                    </a>{" "}
                    to see what <span className="text-red-500">style</span> of opera it
                    is.
                </Paragraph>
            ) : (
                <Paragraph>
                    <strong>Style:</strong> {props.opera.style}
                </Paragraph>
            )}
        </Layout>
    );
};
