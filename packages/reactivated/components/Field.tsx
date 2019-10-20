import React from "react";
import {style} from "typestyle";

import {
    Alert,
    Button,
    FormFeedback,
    FormGroup,
    FormText,
    Input,
    Label,
} from "reactstrap";

import {getValueForSelect, isHidden, Widget, WidgetType} from "./Widget";

const Styles = {
    // Bootstrap hides error messages unless they are general siblings of
    // a form-control. This isn't the case with the autocomplete and other
    // composite widgets. So we force it to always display.
    feedback: style({
        display: "block",
    }),
} as const;

interface FieldType {
    widget: WidgetType;
    label: string;
    help_text: string;
}

interface Props {
    field: FieldType;
    error: string[] | null;
    passed_validation: boolean;
}

export const Field = (props: Props) => {
    const {field, error, passed_validation} = props;

    if (isHidden(field.widget)) {
        return (
            <Widget
                widget={field.widget}
                has_errors={error != null}
                passed_validation={false}
            />
        );
    }
    return (
        <FormGroup>
            <Label for={field.widget.name}>{field.label}</Label>
            <Widget
                widget={field.widget}
                has_errors={error != null}
                passed_validation={passed_validation}
            />
            {field.help_text !== "" && (
                <FormText color="muted">{field.help_text}</FormText>
            )}
            {error != null && (
                <FormFeedback className={Styles.feedback}>
                    {error.map((errorMessage, index) => (
                        <div key={index}>{errorMessage}</div>
                    ))}
                </FormFeedback>
            )}
        </FormGroup>
    );
};
