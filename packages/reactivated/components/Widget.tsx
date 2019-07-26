import React from 'react';

import {classes} from 'typestyle';

import { Button, Form, FormGroup, Label, Input, FormText } from 'reactstrap';
import Downshift from 'downshift'

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

interface DateInput extends BaseWidget {
    template_name: 'django/forms/widgets/date.html';
    type: 'date',
    value: string|null;
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

interface Autocomplete extends BaseWidget {
    value: string[];
    template_name: 'reactivated/autocomplete';
    optgroups: Optgroup[];
}

interface SelectMultiple extends Select {
    attrs: BaseWidget['attrs'] & {
        multiple: 'multiple';
    }
}

export type WidgetType = TextInput|NumberInput|PasswordInput|EmailInput|HiddenInput|Textarea|Select|Autocomplete|SelectMultiple|DateInput;

interface Props {
    widget: WidgetType;
    has_errors: boolean;
    passed_validation: boolean;
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

export const getValueForSelect = (widget: Select|Autocomplete|SelectMultiple) => {
    return isMultiple(widget) ? widget.value : (widget.value[0] || '');
}

export const Widget = (props: Props) => {
    const {className, widget} = props;

    switch (widget.template_name) {
        case "reactivated/autocomplete": {

            const value = getValueForSelect(widget);
            const items = widget.optgroups.map((optgroup, index) => ({value: getValue(optgroup), label: optgroup[1][0].label}));
            const selectedOptgroup = widget.optgroups.filter(optgroup => {return getValue(optgroup).toString() === value})[0];
            const initialSelectedItem = selectedOptgroup != null ? {value: getValue(selectedOptgroup), label: selectedOptgroup[1][0].label} : null;

            const classNames = classes('form-control', {
                'is-invalid': props.has_errors,
                'is-valid': props.passed_validation,
            });

            return <Downshift
                onChange={selection => alert(
                    selection ? `You selected ${selection.value}` : 'Selection Cleared'
                )}
                initialSelectedItem={initialSelectedItem}
                itemToString={item => (item && item.value != '' ? item.label : '')}
            >
                {({
                    getInputProps,
                    getItemProps,
                    getLabelProps,
                    getMenuProps,
                    isOpen,
                    inputValue,
                    highlightedIndex,
                    selectedItem,
                }) =>
                    <div className={classNames}>
                        {/*<label {...getLabelProps()}>Hello</label>*/}
                        <input name={widget.name} defaultValue={selectedItem != null ? selectedItem.value : ''} type="hidden" />
                        <input {...getInputProps()} />
                        <ul {...getMenuProps()}>
                          {isOpen
                            ? items
                                .filter(item => !inputValue || item.value.toString().includes(inputValue))
                                .map((item, index) => (
                                  <li
                                    {...getItemProps({
                                      key: item.value,
                                      index,
                                      item,
                                      style: {
                                        backgroundColor:
                                          highlightedIndex === index ? 'lightgray' : 'white',
                                        fontWeight: selectedItem === item ? 'bold' : 'normal',
                                      },
                                    })}
                                  >
                                    {item.label}
                                  </li>
                                ))
                            : null}
                        </ul>
                    </div>
                }
            </Downshift>;
        }
        case "django/forms/widgets/select.html": {
            /*
            if (isMultiple(widget)) {
                return <div>I am a select multiple</div>;
            }
            */
            // return <div>I am a select single</div>;
            const value = getValueForSelect(widget);

            return <Input
                type="select"
                readOnly={widget.attrs.disabled === true}
                invalid={props.has_errors}
                valid={!!value && props.passed_validation}
                name={widget.name}
                className={className}
                multiple={isMultiple(widget)}
                defaultValue={value}
            >
                {widget.optgroups.map((optgroup, index) =>
                <option key={index} value={getValue(optgroup)}>{optgroup[1][0].label}</option>
                )}
            </Input>;
        }
        case "django/forms/widgets/textarea.html":
            return <Input
                readOnly={widget.attrs.disabled === true}
                invalid={props.has_errors}
                valid={!!widget.value && props.passed_validation}
                type="textarea"
                className={className}
                defaultValue={widget.value || ""}
                id={widget.name}
                name={widget.name}
                rows={10}
            />;
        case "django/forms/widgets/hidden.html":
        case "django/forms/widgets/number.html":
        case "django/forms/widgets/text.html":
        case "django/forms/widgets/password.html":
        case "django/forms/widgets/email.html":
        case "django/forms/widgets/date.html": {
            return <Input
                readOnly={widget.attrs.disabled === true}
                invalid={props.has_errors}
                valid={!!widget.value && props.passed_validation}
                type={widget.type}
                className={className}
                defaultValue={widget.value || ""}
                id={widget.name}
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
