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

export type RequesterResult =
    | {type: "invalid"; errors: any}
    | {type: "success"; data: any}
    | {type: "denied"; reason: any}
    | {type: "unauthorized"}
    | {type: "exception"; exception: unknown};

type JSONValue =
    | string
    | number
    | boolean
    | null
    | JSONValue[]
    | {[key: string]: JSONValue};

export type Requester = (
    url: string,
    payload: JSONValue | null,
    method: "GET" | "POST",
) => Promise<RequesterResult>;

export const defaultRequester: Requester = async (url, payload, method) => {
    try {
        // The method is authoritative (it comes from the server's RPC
        // declaration), not inferred from whether a payload is present. A POST
        // serializes the payload exactly as given — including a literal `null` when
        // the RPC's input is omitted — so the server receives the typed value it
        // expects (e.g. `null` for an optional `Form | None` input).
        const isGet = method === "GET";
        const response = await fetch(url, {
            method,
            body: isGet ? null : JSON.stringify(payload),
            headers: {
                Accept: "application/json",
                ...(isGet ? {} : {"Content-Type": "application/json"}),
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
                reason: await response.json().catch(() => null),
            };
        }

        return {
            type: "exception",
            exception: new Error(`RPC request failed with status ${response.status}`),
        };
    } catch (error) {
        return {
            type: "exception",
            exception: error,
        };
    }
};
