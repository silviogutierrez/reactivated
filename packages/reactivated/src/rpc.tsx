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

export type RequesterResult =
    | {type: "invalid"; errors: any}
    | {type: "success"; data: any}
    | {type: "denied"; reason: any}
    | {type: "unauthorized"}
    | {type: "exception"; exception: unknown};

export type Requester = (url: string, payload: FormData | null) => Promise<RequesterResult>;

export const defaultRequester: Requester = async (url, payload) => {
    try {
        const response = await fetch(url, {
            method: payload == null ? "GET" : "POST",
            body: payload,
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
        } else if (response.status === 401) {
            return {
                type: "unauthorized",
            };
        } else if (response.status === 403) {
            return {
                type: "denied",
                reason: response.json(),
            };
        }
    } catch (error) {
        return {
            type: "exception",
            exception: error,
        };
    }

    return {
        type: "exception",
        exception: null,
    };
};

const buildValues = (
    type: "form" | "form_set",
    formData: FormData,
    prefix: string | null,
    values: any,
) => {
    if (values == null) {
        return;
    }
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
            formData.append(
                prefix == null ? key : `${prefix}-${key}`,
                values[key as keyof typeof values] ?? "",
            ),
        );
    }
};

export async function rpcCall(
    requester: Requester,
    options: {
        url: string;
        input: {
            values: Record<string, any>;
            type: "form" | "form_set" | "form_group";
        } | null;
        paramsAndIterator: ParamsAndIterator | null;
        name: string;
    },
): Promise<Result<any, any, any>> {
    const {url, input, paramsAndIterator, name} = options;
    const {type, values} = input != null ? input : {type: "", values: {}};

    const formData = new FormData();

    if (type === "form_group") {
        Object.keys(values).map((prefix) => {
            const formOrFormSet = (values as any)[prefix];
            if (Array.isArray(formOrFormSet)) {
                buildValues("form_set", formData, prefix, formOrFormSet);
            } else {
                buildValues("form", formData, prefix, formOrFormSet);
            }
        });
    } else if (type === "form_set") {
        buildValues("form_set", formData, "form", values);
    } else {
        buildValues("form", formData, null, values);
    }

    let urlWithPossibleInstance = buildUrl(url, paramsAndIterator);

    if (name != null) {
        urlWithPossibleInstance = urlWithPossibleInstance.concat(`${name}/`);
    }

    const result = await requester(urlWithPossibleInstance, input == null ? null : formData);

    const request: Request = {
        url: urlWithPossibleInstance,
        params: paramsAndIterator?.params,
        name: name,
        data: formData,
    };

    return {...result, request};
}

type Request = {
    url: string;
    params: unknown;
    name: string;
    data: FormData;
};

export type Result<TSuccess, TInvalid, TDenied> =
    | {
          type: "success";
          data: TSuccess;
          request: Request;
      }
    | {
          type: "invalid";
          errors: TInvalid;
          request: Request;
      }
    | {
          type: "denied";
          reason: TDenied;
          request: Request;
      }
    | {
          type: "unauthorized";
          request: Request;
      }
    | {
          type: "exception";
          exception: unknown;
          request: Request;
      };
