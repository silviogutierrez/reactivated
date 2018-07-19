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
    value: string;
    attrs: BaseWidget['attrs'] & {
        maxlength?: number;
    }
}

interface NumberInput extends BaseWidget {
    type: 'number';
    template_name: 'django/forms/widgets/number.html';
    value: string;
    attrs: BaseWidget['attrs'] & {
        step: string;
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

export type WidgetType = TextInput|NumberInput|Select|SelectMultiple;

interface Props {
    widget: WidgetType;
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
    const {widget} = props;

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
                multiple={isMultiple(widget)}
                defaultValue={value}
            >
                {widget.optgroups.map((optgroup, index) =>
                <option key={index} value={getValue(optgroup)}>{optgroup[1][0].label}</option>
                )}
            </select>;
        }
        case "django/forms/widgets/number.html":
        case "django/forms/widgets/text.html": {
            return <input type={widget.type} defaultValue={widget.value || ""} name={widget.name} />;
            // return <div>I am a text</div>;
        }
        default: {
            console.log(widget);
            const _exhaustiveCheck: never = widget;
            throw new Error('Cannot happen');
        }
    }
};
