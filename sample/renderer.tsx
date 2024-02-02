import * as React from "react";

import * as http from "http";
import * as fs from "fs";

type Result =
    | {
          status: "success";
          rendered: string;
      }
    | {
          status: "error";
          error: any;
      };

export const render = async ({
    context,
    props,
}: {
    context: any;
    props: any;
}): Promise<Result> => {
    return {
        status: "success",
        rendered: "This is working",
    };
}

export const serverRender = (body: Buffer) => {
    const {context, props} = JSON.parse(body.toString("utf8"));
    return render({context, props});
};

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

// Relative path to keep it under 100 characters.
// See: https://unix.stackexchange.com/questions/367008/why-is-socket-path-length-limited-to-a-hundred-chars
export const SOCKET_PATH =
    process.env.REACTIVATED_SOCKET ?? `node_modules/_reactivated/reactivated.sock`;

export const server = http.createServer((req, res) => {
    let body = Buffer.from("");

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", async () => {
        const result = await serverRender(body);

        if (result.status === "success") {
            res.writeHead(OK_RESPONSE, {"Content-Type": "text/html; charset=utf-8"});
            res.end(result.rendered);
        } else {
            res.writeHead(ERROR_REPONSE, {"Content-Type": "application/json"});
            res.end(
                JSON.stringify(result.error, Object.getOwnPropertyNames(result.error)),
            );
        }
    });
});

if (fs.existsSync(SOCKET_PATH)) {
    fs.unlinkSync(SOCKET_PATH);
}

server.listen(SOCKET_PATH, () => {
    const address = server.address();

    if (address == null) {
        throw new Error();
    } else if (typeof address === "string") {
        process.stdout.write(`RENDERER:${address}:LISTENING`);
    } else {
        process.stdout.write(`RENDERER:${address.port.toString()}:LISTENING`);
    }
});
