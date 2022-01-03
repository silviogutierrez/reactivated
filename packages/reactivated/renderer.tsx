import {BODY_SIZE_LIMIT, render} from "./server";

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

import http from "http";

const server = http.createServer((req, res) => {
    let body = Buffer.from("");

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", () => {
        const {context, props} = JSON.parse(body.toString("utf8"));
        const result = render({context, props}, null as any, null as any);

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

server.listen(0, () => {
    const address = server.address();

    if (typeof address === "string") {
        throw new Error();
    }
    process.stdout.write(`RENDERER:${address.port.toString()}:LISTENING`);

    // TODO: load this from a passed in parameter.
    // const warmUpTemplate = "HomePage";
    // const templatePath = `${process.cwd()}/client/templates/${warmUpTemplate}`;
    // require(templatePath);
});
