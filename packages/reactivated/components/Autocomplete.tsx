import React from 'react';
import Context from "../context";

import {classes} from 'typestyle';
import {getValueForSelect, getValue, Autocomplete as AutocompleteType, Props as WidgetProps} from './Widget';
import Downshift, {ChildrenFunction} from 'downshift'


interface Props extends WidgetProps {
    widget: AutocompleteType;
}


interface Item {
    value: string|number;
    label: string;
}

interface State {
    isLoading: boolean;
    results: Item[];
}


export class Autocomplete extends React.Component<Props, State> {
    static contextType = Context;

    state = {
        isLoading: false,
        results: [],
    };

    renderMenu: ChildrenFunction<Item> = ({
        getInputProps,
        getItemProps,
        getLabelProps,
        getMenuProps,
        isOpen,
        inputValue,
        highlightedIndex,
        selectedItem,
    }) => {
        const items = this.props.widget.optgroups.map((optgroup, index) => ({value: getValue(optgroup), label: optgroup[1][0].label}));

        if (isOpen) {
            return <>
                {items
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
                }
            </>
        }

        return null;
    }

    handleOnInputValueChange = (value: string) => {
        console.log(this.context);
    }

    render() {
        const {className, widget} = this.props;
        const value = getValueForSelect(widget);
        const items = widget.optgroups.map((optgroup, index) => ({value: getValue(optgroup), label: optgroup[1][0].label}));
        const selectedOptgroup = widget.optgroups.filter(optgroup => {return getValue(optgroup).toString() === value})[0];
        const initialSelectedItem = selectedOptgroup != null ? {value: getValue(selectedOptgroup), label: selectedOptgroup[1][0].label} : null;

        const classNames = classes('form-control', {
            'is-invalid': this.props.has_errors,
            'is-valid': this.props.passed_validation,
        });

        return <Downshift
            onChange={selection => alert(
                selection ? `You selected ${selection.value}` : 'Selection Cleared'
            )}
            onInputValueChange={this.handleOnInputValueChange}
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
                ...otherDownshiftProps
            }) =>
                <div className={classNames}>
                    {/*<label {...getLabelProps()}>Hello</label>*/}
                    <input name={widget.name} defaultValue={selectedItem != null ? selectedItem.value : ''} type="hidden" />
                    <input {...getInputProps()} />

                    <ul {...getMenuProps()}>
                        {this.renderMenu({
                            getInputProps,
                            getItemProps,
                            getLabelProps,
                            getMenuProps,
                            isOpen,
                            inputValue,
                            highlightedIndex,
                            selectedItem,
                            ...otherDownshiftProps,
                        })}
                    </ul>
                </div>
            }
        </Downshift>;
    }
}
