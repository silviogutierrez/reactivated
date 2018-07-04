import React from 'react';

interface Props {
    thing: string;
}

export default (props: Props) => <div>
    I am {props.thing}
</div>;
