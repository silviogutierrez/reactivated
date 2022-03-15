import React from "react";

import {CSRFToken, Iterator, templates, interfaces} from "@reactivated";
import {Layout} from "@client/Layout";

import {useForm, Widget} from "reactivated/forms";

const SPACING = 2;

export default (props: templates.Storyboard) => {
    const handler = useForm({form: props.form});
    const [operas, setOperas] = React.useState<interfaces.OperaList | null>(null);

    const loadOperas = async () => {
        const response = await fetch("/api/operas/", {
            headers: {
                Accept: "application/json",
            },
        });
        const data: interfaces.OperaList = await response.json();

        setOperas(data);
    };

    return (
        <Layout title="Storyboard">
            <h1>Storyboard</h1>
            <form action="" method="POST">
                <CSRFToken />
                <Iterator form={handler}>
                    {(field) => (
                        <>
                            <h2>{field.name}</h2>
                            <p>
                                <Widget field={field} />
                            </p>
                        </>
                    )}
                </Iterator>
                <button type="submit">Submit</button>
            </form>
            <h1>Values</h1>
            <pre>{JSON.stringify(handler.values, null, SPACING)}</pre>
            <h1>Form</h1>
            <pre>{JSON.stringify(props.form, null, SPACING)}</pre>
            <h1>Operas</h1>
            <button onClick={loadOperas}>Load Operas</button>
            <pre>{JSON.stringify(operas, null, SPACING)}</pre>
        </Layout>
    );
};
