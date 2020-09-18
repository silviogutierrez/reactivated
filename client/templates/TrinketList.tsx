import React from "react";

import {Layout} from "../components/Layout";
import {TrinketListProps as Props} from "../models";

export default (props: Props) => (
    <Layout>
        <ul>
            {props.trinket_list.map((widget) => (
                <li key={widget.name}>
                    <a href={widget.url}>{widget.name}</a>
                </li>
            ))}
        </ul>
    </Layout>
);
