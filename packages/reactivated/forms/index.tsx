import React from "react";

export {FormLike, FormSetLike, FieldMap, ManagementForm} from "../components/Form";

import {FieldMap, FormLike} from "../components/Form";
import {SelectDateWidget, WidgetType} from "../components/Widget";

export default <TContext extends {csrf_token: string}>(
    Context: React.Context<TContext>,
) => ({
    CSRFToken: (props: {}) => {
        const context = React.useContext(Context);

        return (
            <input
                type="hidden"
                name="csrfmiddlewaretoken"
                value={context.csrf_token}
            />
        );
    },
});

type FormValue<U extends {value: unknown}> = U extends SelectDateWidget
    ? {[subWidgetName: string]: U["subwidgets"][number]["value"]}
    : U["value"];

export type FormValues<U extends FieldMap> = {
    [K in keyof U]: FormValue<U[K]["widget"]>;
};

const removeSubWidgetPrefix = (field: FieldMap[string], prefixed: string) => {
    const parentWidgetRegex = new RegExp(`^${field.widget.name}_`);
    return prefixed.replace(parentWidgetRegex, "");
};

export const getInitialState = <U extends FieldMap>(
    fieldInterceptor: (form: FormLike<U>, fieldName: keyof U) => U[keyof U],
    iterator: Array<keyof U>,
    form: FormLike<U>,
) => {
    const initialValuesAsEntries = iterator.map((fieldName) => {
        const field = fieldInterceptor(form, fieldName);
        return [fieldName, field.widget.value];
    });

    return Object.fromEntries(initialValuesAsEntries) as FormValues<
        typeof form["fields"]
    >;
};

interface UseForm<U extends FieldMap> {
    form: FormLike<U>;
    iterator?: Array<keyof U>;
    fieldInterceptor?: (form: FormLike<U>, fieldName: keyof U) => U[keyof U];
    changeInterceptor?: (
        name: keyof U,
        prevValues: FormValues<U>,
        nextValues: FormValues<U>,
    ) => FormValues<U>;
}

export interface FormHandler<U extends FieldMap> {
    fieldInterceptor: (form: FormLike<U>, fieldName: keyof U) => U[keyof U];
    errors: NonNullable<{[P in keyof U]?: string[] | undefined}>;
    setValues: React.Dispatch<React.SetStateAction<FormValues<U>>>;
    setErrors: React.Dispatch<
        React.SetStateAction<{[P in keyof U]?: string[] | undefined}>
    >;
    initialState: FormValues<U>;
    handleChange: (name: keyof U, rawValue: unknown | null) => void;
    values: FormValues<U>;
}

/**
 * Lots going on here.
 *
 * @param iterator: the fields to display.
 *
 * @param fieldInterceptor: an optional way to mutate a field prior to rendering it.
 * Useful to disable fields conditionally.
 *
 * @param setValues: a way to bubble up values, like in formsets. This is not
 * the actual way to set the canonical values for the form.
 *
 * @param changeInterceptor: a way to catch values that are about to be updated
 * including the name of the changed value. This lets us revert values, mutate
 * them, and blank out other values based on a change.
 */
export const useForm = <U extends FieldMap>(options: UseForm<U>): FormHandler<U> => {
    const iterator = options.iterator ?? options.form.iterator;
    const fieldInterceptor =
        options.fieldInterceptor ?? ((form, fieldName) => form.fields[fieldName]);
    const initialState = getInitialState(fieldInterceptor, iterator, options.form);
    const changeInterceptor =
        options.changeInterceptor ?? ((_, prevValues, nextValues) => nextValues);

    const [values, setValues] = React.useState(() => {
        return initialState;
    });

    // For our changeHandler, we need both the top level widget and the subwidget so we know what our
    // value processor needs to return. For subwidgets, our value processor needs to return an object.

    // For top level widgets, it can just return the value itself.
    const handleChange = (name: keyof U, rawValue: unknown | null) => {
        const value = (rawValue ?? "") as string;
        console.log(name, value);

        /*
         * TODO: handle select, subwidgets, etc.
         *
        const processedValue =
            subwidget.template_name === "django/forms/widgets/select.html" ||
            (subwidget.template_name as "quick") === "quick"
                ? [value.toString()]
                : value.toString();
        */

        // We need the callback syntax to make sure we have the latest values on a form.
        setValues((prevValues) => {
            const nextValues = changeInterceptor(name, prevValues, {
                ...prevValues,
                [name]: value,
            });

            return nextValues;
        });
    };

    const initialErrors =
        options.form.errors ?? ({} as NonNullable<typeof options.form.errors>);

    const [errors, setErrors] = React.useState(initialErrors);

    return {
        fieldInterceptor,
        errors,
        setErrors,
        setValues,
        initialState,
        handleChange,
        values,
    };
};

interface BaseFieldsProps<U extends FieldMap> {
    fieldInterceptor?: (form: FormLike<U>, fieldName: keyof U) => U[keyof U];
    changeInterceptor?: (
        name: keyof U,
        prevValues: FormValues<U>,
        nextValues: FormValues<U>,
    ) => FormValues<U>;
    form: FormLike<U>;
    children: (
        props: FormHandler<U> & {error: string[] | null; field: U[keyof U]},
    ) => React.ReactNode;
}

interface IncludeFieldsProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: Array<keyof U>;
    exclude?: never;
}

interface ExcludeFieldProps<U extends FieldMap> extends BaseFieldsProps<U> {
    fields?: never;
    exclude: Array<keyof U>;
}

type FieldsProps<U extends FieldMap> = IncludeFieldsProps<U> | ExcludeFieldProps<U>;

export const Fields = <U extends FieldMap>(props: FieldsProps<U>) => {
    const getField =
        props.fieldInterceptor ?? ((form, fieldName) => form.fields[fieldName]);

    const getIterator = () => {
        if (props.fields != null) {
            return props.fields;
        }

        if (props.exclude != null) {
            return props.form.iterator.filter(
                (field) => !props.exclude.includes(field),
            );
        }

        return props.form.iterator;
    };

    const iterator = getIterator();
    const handler = useForm({...props, iterator});

    return (
        <>
            {iterator
                .map(
                    (fieldName) =>
                        [
                            fieldName,
                            handler.fieldInterceptor(props.form, fieldName),
                        ] as const,
                )
                .map(([fieldName, field]) => {
                    const {widget} = field;
                    const error =
                        handler.errors != null
                            ? handler.errors[fieldName] ?? null
                            : null;

                    return (
                        <React.Fragment key={fieldName.toString()}>
                            {props.children({field, error, ...handler})}
                        </React.Fragment>
                    );
                })}
        </>
    );
};
