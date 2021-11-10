import React from "react";
import {Types} from "../generated";

type Optgroup = Types["Optgroup"];

export const CheckboxInput = (props: {
    name: string;
    value: true | false;
    onChange: (value: boolean) => void;
}) => {
    return (
        <input
            type="checkbox"
            name={props.name}
            checked={props.value}
            onChange={(event) => props.onChange(event.target.checked)}
        />
    );
};

export const TextInput = (props: {
    name: string;
    value: string | null;
    onChange: (value: string) => void;
}) => {
    return (
        <input
            type="text"
            name={props.name}
            value={props.value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        />
    );
};

export const Select = (props: {
    name: string;
    value: string | number | null;
    optgroups: Optgroup[];
    onChange: (value: string) => void;
}) => {
    const {name, optgroups, value} = props;

    return (
        <select
            key={name}
            name={name}
            value={value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        >
            {optgroups.map((optgroup) => {
                const value = (optgroup[1][0].value ?? "").toString();
                return (
                    <option key={value} value={value}>
                        {optgroup[1][0].label}
                    </option>
                );
            })}
        </select>
    );
};