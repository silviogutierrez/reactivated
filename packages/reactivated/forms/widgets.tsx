import React from "react";
import {Types} from "../generated";

export type CoreWidget = Types["Widget"];

type Optgroup = Types["Optgroup"];

export const CheckboxInput = (props: {
    name: string;
    className?: string;
    value: true | false;
    onChange: (value: boolean) => void;
}) => {
    return (
        <input
            type="checkbox"
            name={props.name}
            className={props.className}
            checked={props.value}
            onChange={(event) => props.onChange(event.target.checked)}
        />
    );
};

export const TextInput = (props: {
    name: string;
    className?: string;
    value: string | null;
    onChange: (value: string) => void;
}) => {
    return (
        <input
            type="text"
            name={props.name}
            className={props.className}
            value={props.value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        />
    );
};

export const Select = (props: {
    name: string;
    className?: string;
    value: string | number | null;
    optgroups: Optgroup[];
    onChange: (value: string) => void;
}) => {
    const {name, optgroups, value} = props;

    return (
        <select
            key={name}
            name={name}
            className={props.className}
            value={value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        >
            {optgroups.map((optgroup) => {
                const optgroupValue = (optgroup[1][0].value ?? "").toString();
                return (
                    <option key={optgroupValue} value={optgroupValue}>
                        {optgroup[1][0].label}
                    </option>
                );
            })}
        </select>
    );
};

export const Textarea = (props: {
    name: string;
    className?: string;
    value: string | null;
    onChange: (value: string) => void;
}) => {
    return (
        <textarea
            name={props.name}
            className={props.className}
            value={props.value ?? ""}
            onChange={(event) => props.onChange(event.target.value)}
        />
    );
};
