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
) => Promise<RequesterResult>;

export const defaultRequester: Requester = async (url, payload) => {
    try {
        const response = await fetch(url, {
            method: payload == null ? "GET" : "POST",
            body: payload == null ? null : JSON.stringify(payload),
            headers: {
                Accept: "application/json",
                ...(payload != null ? {"Content-Type": "application/json"} : {}),
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
