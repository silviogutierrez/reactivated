import React from 'react';

interface BaseWidget {
    name: string;
    is_hidden: boolean;
    required: boolean;
    attrs: {
        id: string;
        disabled?: boolean;
        required?: boolean;
    };
}

interface TextInput extends BaseWidget {
    type: 'text';
    template_name: 'django/forms/widgets/text.html';
    value: string|null;
    attrs: BaseWidget['attrs'] & {
        maxlength?: number;
    }
}

interface NumberInput extends BaseWidget {
    type: 'number';
    template_name: 'django/forms/widgets/number.html';
    value: string|null;
    attrs: BaseWidget['attrs'] & {
        step: string;
    }
}

interface PasswordInput extends BaseWidget {
    type: 'password';
    template_name: 'django/forms/widgets/password.html';
    value: string|null;
}

interface EmailInput extends BaseWidget {
    type: 'email';
    template_name: 'django/forms/widgets/email.html';
    value: string|null;
}

interface HiddenInput extends BaseWidget {
    type: 'hidden';
    template_name: 'django/forms/widgets/hidden.html';
    value: string|null;
}

interface Textarea extends BaseWidget {
    template_name: 'django/forms/widgets/textarea.html';
    value: string|null;
    attrs: BaseWidget['attrs'] & {
        cols: string;
        rows: string;
    }
}


type Optgroup = [
    null,
    [
        {
            name: string;
            // value: string|number|boolean|null;
            value: string|number|boolean|null;
            label: string;
            selected: boolean;
        }
    ],
    number
]

type IsMultiple = {attrs: {multiple: 'multiple'}};

type IsSingle = {attrs: {}};

function isMultiple<T extends IsMultiple, U extends IsSingle>(widget: T|U): widget is T {
    return 'multiple' in widget.attrs;
}

interface Select extends BaseWidget {
    value: string[];
    template_name: 'django/forms/widgets/select.html';
    optgroups: Optgroup[];
}

interface SelectMultiple extends Select {
    attrs: BaseWidget['attrs'] & {
        multiple: 'multiple';
    }
}

export type WidgetType = TextInput|NumberInput|PasswordInput|EmailInput|HiddenInput|Textarea|Select|SelectMultiple;

interface Props {
    widget: WidgetType;
    className?: string;
}

const getValue = (optgroup: Optgroup) => {
    const rawValue = optgroup[1][0].value;

    if (rawValue == null) {
        return '';
    }
    else if (rawValue === true) {
        return 'True';
    }
    else if (rawValue === false) {
        return 'False';
    }
    return rawValue;
}

export const Widget = (props: Props) => {
    const {className, widget} = props;

    switch (widget.template_name) {
        case "django/forms/widgets/select.html": {
            /*
            if (isMultiple(widget)) {
                return <div>I am a select multiple</div>;
            }
            */
            // return <div>I am a select single</div>;
            const value = isMultiple(widget) ? widget.value : (widget.value[0] || '');
            return <select
                name={widget.name}
                className={className}
                multiple={isMultiple(widget)}
                defaultValue={value}
            >
                {widget.optgroups.map((optgroup, index) =>
                <option key={index} value={getValue(optgroup)}>{optgroup[1][0].label}</option>
                )}
            </select>;
        }
        case "django/forms/widgets/textarea.html":
            return <textarea name={widget.name} className={className} defaultValue={widget.value || ""} />
        case "django/forms/widgets/hidden.html":
        case "django/forms/widgets/number.html":
        case "django/forms/widgets/text.html":
        case "django/forms/widgets/password.html":
        case "django/forms/widgets/email.html": {
            return <input
                readOnly={widget.attrs.disabled === true}
                type={widget.type}
                className={className}
                defaultValue={widget.value || ""}
                name={widget.name}
            />;
            // return <div>I am a text</div>;
        }
        default: {
            const _exhaustiveCheck: never = widget;
            throw new Error('Cannot happen, unknown widget type: \n' + JSON.stringify(widget, null, 2));
        }
    }
};
