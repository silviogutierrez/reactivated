export type WidgetLike = {
    name: string;
    tag: string;
    subwidgets?: WidgetLike[];
    value: unknown;
};

interface Field {
    name: string;
    widget: WidgetLike;
    label: string;
    help_text: string;
}

export interface FieldMap {
    [name: string]: Field;
}

export interface FormLike<T extends FieldMap> {
    name: string;
    fields: T;
    errors: {[P in keyof T]?: string[]} | null;
    iterator: Array<Extract<keyof T, string>>;
    prefix: string;
}

export type FormValues<U extends FieldMap> = {
    [K in keyof U]: U[K] extends {enum: unknown}
        ? U[K]["enum"] | null
        : U[K]["widget"]["value"];
};

export interface FormHandler<T extends FieldMap> {
    form: FormLike<T>;
    values: FormValues<T>;
}

export const useForm = <T extends FieldMap>({
    form,
}: {
    form: FormLike<T>;
}): FormHandler<T> => {
    return null as any;
};
