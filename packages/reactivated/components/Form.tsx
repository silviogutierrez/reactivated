import React from "react";

import {getValueForSelect, WidgetType} from "./Widget";

interface FieldLike {
    name: string;
    widget: {name: string; value: unknown};
    label: string;
    help_text: string;
}

/*
interface Form {
    fields: {
        [name: string]: FieldLike;
    },
    errors: {
        [P in keyof this['fields']]: string[]|null;
    }
    iterator: Array<keyof this['fields']>;
}
*/

export interface FieldMap {
    [name: string]: FieldLike;
}

export interface FormLike<T extends FieldMap> {
    name: string;
    fields: T;
    errors: {[P in keyof T]?: string[]} | null;
    iterator: Array<keyof T>;
    prefix: string;
}

export interface FormSetLike<T extends FieldMap> {
    initial: number;
    total: number;
    max_num: number;
    min_num: number;
    can_delete: boolean;
    can_order: boolean;
    non_form_errors: string[];

    // Technically we don't need management form.
    // Since we have ManagementForm as a component that uses initial and total.
    management_form: unknown;
    prefix: string;

    forms: Array<FormLike<T>>;
    empty_form: FormLike<T>;
}

export const ManagementForm = <T extends FieldMap>({
    formSet,
}: {
    formSet: FormSetLike<T>;
}) => {
    return (
        <>
            <input
                type="hidden"
                name={`${formSet.prefix}-INITIAL_FORMS`}
                value={formSet.initial}
            />
            <input
                type="hidden"
                name={`${formSet.prefix}-TOTAL_FORMS`}
                value={formSet.total}
            />
        </>
    );
};
