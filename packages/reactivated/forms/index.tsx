import React from "react";

export {FormLike, FormSetLike, ManagementForm} from "../components/Form";

import {FormLike, FieldMap} from "../components/Form";
import {WidgetType, SelectDateWidget} from "../components/Widget";
import Context from "../context";

export const CSRFToken = (props: {}) => {
    const context = React.useContext(Context);

    return (
        <input type="hidden" name="csrfmiddlewaretoken" value={context.csrf_token} />
    );
};

type FormValue<U extends WidgetType> = U extends SelectDateWidget
    ? {[subWidgetName: string]: U["subwidgets"][number]["value"]}
    : U["value"];

export type FormValues<U extends FieldMap> = {
    [K in keyof U]: FormValue<U[K]["widget"]>;
};

interface BaseFieldsProps<U extends FieldMap> {
    changeInterceptor?: (
        name: keyof U,
        prevValues: FormValues<U>,
        nextValues: FormValues<U>,
    ) => FormValues<U>;
    form: FormLike<U>;
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
    return <div>Ok</div>;
};
