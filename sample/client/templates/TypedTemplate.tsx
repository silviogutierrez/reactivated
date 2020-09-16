import React from "react";
import {style} from "typestyle";

import {Layout} from "@client/components/Layout";
import {Types} from "@client/generated";

const styles = {
    layout: style({maxWidth: 600, margin: "0 auto"}),

    header: style({color: "blue"}),
} as const;

export default class extends React.Component<Types["TypedTemplateProps"], {}> {
    render() {
        const props = this.props;

        return (
            <Layout title="Typed template example">
                <div className={styles.layout}>
                    <h1>
                        {props.opera.name} by {props.composer.name}
                    </h1>
                    <h2>Countries {props.composer.name} libed in:</h2>
                    <ul>
                        {props.composer.countries.map((country) => (
                            <li key={country.id}>{country.name}</li>
                        ))}
                    </ul>
                </div>
            </Layout>
        );
    }
}
