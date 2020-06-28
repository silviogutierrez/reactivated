import React from "react";

import {classes} from "typestyle";

import {Button, Form, FormGroup, FormText, Input, Label} from "reactstrap";
import {Autocomplete as AutocompleteWidget} from "./Autocomplete";

const TEXTAREA_ROWS = 10;

interface BaseWidget {
    name: string;
    is_hidden: boolean;
    required: boolean;
    attrs: {
        id: string;
        placeholder?: string;
        disabled?: boolean;
        required?: boolean;
    };
}

export interface TextInput extends BaseWidget {
    type: "text";
    template_name: "django/forms/widgets/text.html";
    value: string | null;
    attrs: BaseWidget["attrs"] & {
        maxlength?: string;
    };
}

export interface NumberInput extends BaseWidget {
    type: "number";
    template_name: "django/forms/widgets/number.html";
    value: string | null;
    attrs: BaseWidget["attrs"] & {
        step: string;
    };
}

export interface PasswordInput extends BaseWidget {
    type: "password";
    template_name: "django/forms/widgets/password.html";
    value: string | null;
}

export interface EmailInput extends BaseWidget {
    type: "email";
    template_name: "django/forms/widgets/email.html";
    value: string | null;
}

export interface HiddenInput extends BaseWidget {
    type: "hidden";
    template_name: "django/forms/widgets/hidden.html";
    value: string | null;
}

export interface Textarea extends BaseWidget {
    template_name: "django/forms/widgets/textarea.html";
    value: string | null;
    attrs: BaseWidget["attrs"] & {
        cols: string;
        rows: string;
    };
}

export interface DateInput extends BaseWidget {
    template_name: "django/forms/widgets/date.html";
    type: "date";
    value: string | null;
}

export interface ClearableFileInput extends BaseWidget {
    template_name: "django/forms/widgets/clearable_file_input.html";
    type: "file";
    value: string | null;
    checkbox_name: string;
    checkbox_id: string;
    is_initial: boolean;
    input_text: string;
    initial_text: string;
    clear_checkbox_label: string;
}

type Optgroup = [
    null,
    [
        {
            name: string;
            // value: string|number|boolean|null;
            value: string | number | boolean | null;
            label: string;
            selected: boolean;
        },
    ],
    number,
];

interface IsMultiple {
    attrs: {multiple: "multiple"};
}

interface IsSingle {
    attrs: {};
}

function isMultiple<T extends IsMultiple, U extends IsSingle>(
    widget: T | U,
): widget is T {
    return "multiple" in widget.attrs;
}

export interface Select extends BaseWidget {
    value: string[];
    template_name: "django/forms/widgets/select.html";
    optgroups: Optgroup[];
}

export interface Autocomplete extends BaseWidget {
    value: string[];
    template_name: "reactivated/autocomplete";
    selected: {
        value: string | number;
        label: string;
    } | null;
}

export interface SelectMultiple extends Select {
    attrs: BaseWidget["attrs"] & {
        multiple: "multiple";
    };
}

export interface SelectDateWidget extends BaseWidget {
    value: {
        year: string | null;
        month: string | null;
        day: string | null;
    };
    subwidgets: [Select, Select, Select];
    template_name: "django/forms/widgets/select_date.html";
}

export type WidgetType =
    | TextInput
    | NumberInput
    | PasswordInput
    | EmailInput
    | HiddenInput
    | Textarea
    | Select
    | Autocomplete
    | SelectMultiple
    | DateInput
    | SelectDateWidget
    | ClearableFileInput;

export interface Props {
    widget: WidgetType;
    has_errors: boolean;
    passed_validation: boolean;
    className?: string;
}

export const getValue = (optgroup: Optgroup) => {
    const rawValue = optgroup[1][0].value;

    if (rawValue == null) {
        return "";
    } else if (rawValue === true) {
        return "True";
    } else if (rawValue === false) {
        return "False";
    }
    return rawValue;
};

export const getValueForSelect = (widget: Select | Autocomplete | SelectMultiple) => {
    if (isMultiple(widget)) {
        return widget.value;
    } else {
        return widget.value == null ? "" : widget.value[0];
    }
};

export const isHidden = (widget: WidgetType) =>
    "type" in widget && widget.type === "hidden";

export const Widget = (props: Props) => {
    const {className, widget} = props;

    switch (widget.template_name) {
        case "reactivated/autocomplete": {
            return <AutocompleteWidget {...props} widget={widget} />;
        }
        case "django/forms/widgets/select.html": {
            /*
            if (isMultiple(widget)) {
                return <div>I am a select multiple</div>;
            }
            */
            // return <div>I am a select single</div>;
            const value = getValueForSelect(widget);

            return (
                <Input
                    type="select"
                    readOnly={widget.attrs.disabled === true}
                    invalid={props.has_errors}
                    valid={value !== "" && value !== [] && props.passed_validation}
                    name={widget.name}
                    className={className}
                    multiple={isMultiple(widget)}
                    defaultValue={value}
                >
                    {widget.optgroups.map((optgroup, index) => (
                        <option key={index} value={getValue(optgroup)}>
                            {optgroup[1][0].label}
                        </option>
                    ))}
                </Input>
            );
        }
        case "django/forms/widgets/textarea.html":
            return (
                <Input
                    readOnly={widget.attrs.disabled === true}
                    invalid={props.has_errors}
                    valid={
                        widget.value !== "" &&
                        widget.value != null &&
                        props.passed_validation
                    }
                    type="textarea"
                    className={className}
                    defaultValue={widget.value != null ? widget.value : ""}
                    id={widget.name}
                    name={widget.name}
                    rows={TEXTAREA_ROWS}
                />
            );
        case "django/forms/widgets/select_date.html":
            throw new Error(
                "SelectDate has no default JSX implementation. Write your own",
            );
        case "django/forms/widgets/clearable_file_input.html":
        case "django/forms/widgets/hidden.html":
        case "django/forms/widgets/number.html":
        case "django/forms/widgets/text.html":
        case "django/forms/widgets/password.html":
        case "django/forms/widgets/email.html":
        case "django/forms/widgets/date.html": {
            return (
                <Input
                    readOnly={widget.attrs.disabled === true}
                    invalid={props.has_errors}
                    valid={
                        widget.value !== "" &&
                        widget.value != null &&
                        props.passed_validation
                    }
                    type={widget.type}
                    className={className}
                    defaultValue={widget.value != null ? widget.value : ""}
                    id={widget.name}
                    name={widget.name}
                />
            );
            // return <div>I am a text</div>;
        }
        default: {
            const exhaustiveCheck: never = widget;
            throw new Error(
                "Cannot happen, unknown widget type: \n" +
                    JSON.stringify(widget, null, 4), // tslint:disable-line
            );
        }
    }
};
