import React from "react";

import {Layout} from "../components/Layout";

export default () => <Layout>
    <h1>Hello World</h1>
    <button onClick={() => alert("working")}>Click me</button>
</Layout>
