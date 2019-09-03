import React from 'react';
import {style} from 'typestyle';

import {Alert, Button, FormGroup, Label, Input, FormText, FormFeedback} from 'reactstrap';

import {Widget, WidgetType, getValueForSelect} from './Widget';


const Styles = {
    // Bootstrap hides error messages unless they are general siblings of
    // a form-control. This isn't the case with the autocomplete and other
    // composite widgets. So we force it to always display.
    feedback: style({
        display: 'block',
    }),
} as const;


interface FieldType {
    widget: WidgetType;
    prefix: string;
    label: string;
    help_text: string;
};

interface Props {
    field: FieldType;
    error: string[]|null;
    passed_validation: boolean;
}

export const Field = (props: Props) => {
    const {field, error, passed_validation} = props;

    if ('type' in field.widget && field.widget.type === 'hidden') {
        return <Widget widget={field.widget} has_errors={error != null} passed_validation={false} />
    }
    return <FormGroup>
        <Label for={field.widget.name}>{field.label}</Label>
        <Widget widget={field.widget} has_errors={error != null} passed_validation={passed_validation} />
        {field.help_text !== '' &&
        <FormText color="muted">
            {field.help_text}
        </FormText>
        }
        {error != null &&
        <FormFeedback className={Styles.feedback}>
            {error.map((error, index) =>
            <div key={index}>{error}</div>
            )}
        </FormFeedback>
        }
    </FormGroup>

};
