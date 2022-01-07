import React from "react";

import {Layout} from "@client/components/Layout";

export default () => (
    <Layout title="Hello World">
        <h1>Hello World</h1>
        <button onClick={() => alert("working")}>Click me</button>
    </Layout>
);
