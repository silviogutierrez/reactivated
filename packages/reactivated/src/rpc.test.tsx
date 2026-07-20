// Run with: npm exec -- jiti packages/reactivated/src/rpc.test.tsx
// jiti (a declared dependency) transpiles this .tsx; node's built-in test
// runner is avoided because jiti rewrites the "node:test" specifier to a bare
// "test" require, which does not resolve.
import assert from "node:assert/strict";

import {RequesterResult, defaultRequester} from "./rpc";

type MockResponse = {
    status: number;
    json: () => Promise<unknown>;
};

const globals = globalThis as {
    fetch: typeof fetch;
    document?: {cookie: string};
};
const originalFetch = globals.fetch;

// defaultRequester reads document.cookie for the CSRF token.
globals.document = {cookie: "csrftoken=token"};

const stubFetch = (response: MockResponse): void => {
    globals.fetch = (async () => response) as unknown as typeof fetch;
};

const call = (): Promise<RequesterResult> =>
    defaultRequester("/rpc/example/", null, "POST");

const cases: Array<[string, () => Promise<void>]> = [
    [
        "200 -> success with parsed data",
        async () => {
            stubFetch({status: 200, json: async () => ({ok: true})});
            const result = await call();
            assert.equal(result.type, "success");
            assert.deepEqual(result.type === "success" && result.data, {ok: true});
        },
    ],
    [
        "400 -> invalid with parsed errors",
        async () => {
            stubFetch({status: 400, json: async () => ["bad"]});
            const result = await call();
            assert.equal(result.type, "invalid");
            assert.deepEqual(result.type === "invalid" && result.errors, ["bad"]);
        },
    ],
    [
        "401 -> unauthorized",
        async () => {
            stubFetch({status: 401, json: async () => ({error: "UNAUTHORIZED"})});
            const result = await call();
            assert.equal(result.type, "unauthorized");
        },
    ],
    [
        "403 with JSON -> denied, reason resolved (not a Promise)",
        async () => {
            stubFetch({status: 403, json: async () => ({detail: "nope"})});
            const result = await call();
            assert.equal(result.type, "denied");
            if (result.type === "denied") {
                assert.ok(!(result.reason instanceof Promise));
                assert.deepEqual(result.reason, {detail: "nope"});
            }
        },
    ],
    [
        "403 without JSON -> denied, reason null",
        async () => {
            stubFetch({
                status: 403,
                json: async () => {
                    throw new SyntaxError("Unexpected end of JSON input");
                },
            });
            const result = await call();
            assert.equal(result.type, "denied");
            if (result.type === "denied") {
                assert.equal(result.reason, null);
            }
        },
    ],
    [
        "500 -> exception carrying an Error mentioning the status",
        async () => {
            stubFetch({status: 500, json: async () => ({})});
            const result = await call();
            assert.equal(result.type, "exception");
            if (result.type === "exception") {
                assert.ok(result.exception instanceof Error);
                assert.match((result.exception as Error).message, /500/);
            }
        },
    ],
    [
        "thrown fetch error -> exception carrying the thrown error",
        async () => {
            const networkError = new TypeError("network down");
            globals.fetch = (async () => {
                throw networkError;
            }) as unknown as typeof fetch;
            const result = await call();
            assert.equal(result.type, "exception");
            assert.equal(result.type === "exception" && result.exception, networkError);
        },
    ],
];

const run = async (): Promise<void> => {
    let failures = 0;
    for (const [name, fn] of cases) {
        try {
            await fn();
            console.log(`  ok   ${name}`);
        } catch (error) {
            failures += 1;
            console.error(`  FAIL ${name}`);
            console.error(error);
        } finally {
            globals.fetch = originalFetch;
        }
    }
    console.log(
        `\ndefaultRequester: ${cases.length - failures}/${cases.length} passed`,
    );
    process.exit(failures === 0 ? 0 : 1);
};

void run();
