import React from 'react';

import {Widget, WidgetType} from './Widget';

interface Field {
    widget: WidgetType;
}

export type FormType = Field[];

interface Props {
    form: FormType;
}

export const Form = (props: Props) => {
    return <div>
        {props.form.map(field => <Widget key={field.widget.name} widget={field.widget} />)}
    </div>;
};
