// lets us specify the cookie string rather than always looking at
// document.cookie.
export function getCookieFromCookieString(name: string, cookieString: string) {
    let cookieValue = null;
    if (cookieString && cookieString != "") {
        const cookies = cookieString.split(";");
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == name + "=") {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

type ParamsAndIterator = {iterator: string[]; params: Record<string, string | number>};

function buildUrl(baseUrl: string, paramsAndIterator: ParamsAndIterator | null) {
    if (paramsAndIterator == null) {
        return baseUrl;
    } else {
        const params = [];

        for (const key of paramsAndIterator.iterator) {
            params.push(paramsAndIterator.params[key]);
        }

        return `${baseUrl}${params.join("/")}/`;
    }
}

const buildValues = (type: "form" | "form_set", formData: FormData, prefix: string | null, values: any) => {
    if (type === "form_set") {
        // TODO: can initial always be 0?
        formData.append(`${prefix}-INITIAL_FORMS`, values.length);
        formData.append(`${prefix}-TOTAL_FORMS`, values.length);
        for (const index in values as Array<any>) {
            const formSetForm = values[index];
            Object.keys(formSetForm).forEach((key) =>
                formData.append(`${prefix}-${index}-${key}`, formSetForm[key] ?? ""),
            );
        }
    } else {
        Object.keys(values).forEach((key) =>
            formData.append(prefix == null ? key : `${prefix}-${key}`, values[key as keyof typeof values] ?? ""),
        );
    }
}

export async function rpcCall(options: {
    url: string;
    input: {
        values: Record<string, any>;
        type: "form" | "form_set" | "form_group";
    } | null;
    paramsAndIterator: ParamsAndIterator | null;
    name: string | null;
}): Promise<Result<any, any>> {
    const {url, input, paramsAndIterator, name} = options;
    const {type, values} = input != null ? input : {type: "", values: {}};

    const formData = new FormData();

    if (type === "form_group") {
        Object.keys(values).map((prefix) => {
            const formOrFormSet = (values as any)[prefix];
            if (Array.isArray(formOrFormSet)) {
                buildValues("form_set", formData, prefix, formOrFormSet)
            }
            else {
                buildValues("form", formData, prefix, formOrFormSet)
            }
        })
    }
    else if (type === "form_set") {
        buildValues("form_set", formData, "form", values);
    } else {
        buildValues("form", formData, null, values)
    }

    let urlWithPossibleInstance = buildUrl(url, paramsAndIterator);

    if (name != null) {
        urlWithPossibleInstance = urlWithPossibleInstance.concat(`${name}/`);
    }

    try {
        const response = await fetch(urlWithPossibleInstance, {
            method: "POST",
            body: formData,
            headers: {
                Accept: "application/json",
                "X-CSRFToken":
                    getCookieFromCookieString("csrftoken", document.cookie) ?? "",
            },
        });

        if (response.status === 200) {
            return {
                type: "success",
                data: await response.json(),
            };
        } else if (response.status === 400) {
            return {
                type: "invalid",
                errors: await response.json(),
            };
        }

        throw new Error("Unknown status code");
    } catch (exception: unknown) {
        return {
            type: "exception",
            exception,
        };
    }
}

export type Result<TSuccess, TInvalid> =
    | {
          type: "success";
          data: TSuccess;
      }
    | {
          type: "invalid";
          errors: TInvalid;
      }
    | {
          type: "exception";
          exception: unknown;
      };
