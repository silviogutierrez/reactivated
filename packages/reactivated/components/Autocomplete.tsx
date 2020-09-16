import React from "react";
import Context from "../context";

import {classes, style} from "typestyle";
import {
    Autocomplete as AutocompleteType,
    getValue,
    getValueForSelect,
    Props as WidgetProps,
} from "./Widget";

import Downshift, {ChildrenFunction} from "downshift";
import {Input} from "reactstrap";

const Styles = {
    autocomplete: style({
        position: "relative",
    }),
    menu: style({
        position: "absolute",
        margin: 0,
        maxHeight: "20rem",
        overflowY: "auto",
        overflowX: "hidden",
        outline: 0,
        width: "100%",
        padding: 0,
        backgroundColor: "white",
        border: "1px solid #CCC",
    }),

    empty: style({
        fontStyle: "italic",
    }),

    menuItem: style({
        listStyleType: "none",
        padding: "5px",
    }),
} as const;

interface Props extends WidgetProps {
    widget: AutocompleteType;
}

interface Item {
    value: string | number;
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
        results: [] as Item[],
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
        // const items = this.props.widget.optgroups.map((optgroup, index) => ({value: getValue(optgroup), label: optgroup[1][0].label}));
        const items = this.state.results;

        if (items.length === 0) {
            return (
                <li className={classes(Styles.menuItem, Styles.empty)}>
                    No matching items
                </li>
            );
        }

        return (
            <>
                {items
                    // .filter(item => !inputValue || item.value.toString().includes(inputValue))
                    .map((item, index) => (
                        <li
                            className={Styles.menuItem}
                            {...getItemProps({
                                key: item.value,
                                index,
                                item,
                                style: {
                                    backgroundColor:
                                        highlightedIndex === index
                                            ? "lightgray"
                                            : "white",
                                    fontWeight:
                                        selectedItem != null &&
                                        selectedItem.value === item.value
                                            ? "bold"
                                            : "normal",
                                },
                            })}
                        >
                            {item.label}
                        </li>
                    ))}
            </>
        );
    };

    handleOnInputValueChange = async (value: string) => {
        const url = new URL(this.context.request.url);
        url.searchParams.append("autocomplete", this.props.widget.name);
        url.searchParams.append("query", value);

        return fetch(url.toString())
            .then((response) => response.json())
            .then(({results}) => {
                this.setState({results});
            });
    };

    render() {
        const {props} = this;
        const {className, widget} = this.props;

        return (
            <Downshift
                onInputValueChange={this.handleOnInputValueChange}
                initialSelectedItem={widget.selected}
                itemToString={(item) => (item && item.value !== "" ? item.label : "")}
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
                }) => (
                    <div className={Styles.autocomplete}>
                        {/*<label {...getLabelProps()}>Hello</label>*/}
                        <input
                            name={widget.name}
                            defaultValue={
                                selectedItem != null ? selectedItem.value : ""
                            }
                            type="hidden"
                        />
                        <Input
                            invalid={props.has_errors}
                            valid={widget.value.length > 0 && props.passed_validation}
                            {...getInputProps()}
                        />

                        {isOpen && (
                            <ul className={Styles.menu} {...getMenuProps()}>
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
                        )}
                    </div>
                )}
            </Downshift>
        );
    }
}
