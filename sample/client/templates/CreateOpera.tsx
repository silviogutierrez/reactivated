import React, {useDebugValue} from "react";

import {Layout} from "@client/components/Layout";
import {forms, Types, ReactivatedSerializationTextInput} from "@client/generated";
// import {Form} from "@client/forms";
// import {useForm, FormLike, FormHandler, FieldMap} from "reactivated/forms";


export default (props: Types["CreateOperaProps"]) => {
    return (
        <Layout title="Create opera">
            <form method="POST" action="">
                <forms.CSRFToken />
                <div style={{display: "flex"}}>
                    <forms.Form form={props.form} />
                    <forms.Form form={props.pre_filled} />
                    <forms.Form form={props.posted} />
                </div>
                <input type="submit" value="Submit" />
            </form>
        </Layout>
    );
};
