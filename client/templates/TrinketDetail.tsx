import React from 'react';

import {Layout} from '../components/Layout';
import {TrinketDetailProps as Props} from '../models';


export default (props: Props) => <Layout>
    <h1>{props.trinket.name}</h1>
    <a href={props.back_url}>Back to list</a>
</Layout>;
