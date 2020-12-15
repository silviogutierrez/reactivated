import React from "react";

import {classes} from "typestyle";

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

export interface CheckboxInput extends BaseWidget {
    type: "number";
    template_name: "django/forms/widgets/checkbox.html";
    value: string | null;
    attrs: BaseWidget["attrs"] & {
        checked?: true;
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

export interface Select<T extends string = string> extends BaseWidget {
    value: T[];
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

export interface SelectMultiple<T extends string = string> extends Select<T> {
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
    | CheckboxInput
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
