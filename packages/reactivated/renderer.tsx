import {BODY_SIZE_LIMIT, render} from "./server";

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

import http from "http";

const server = http.createServer((req, res) => {
    let body = Buffer.from(""); // , 'utf8');

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", () => {
        res.writeHead(OK_RESPONSE, {"Content-Type": "text/html"});
        res.end(render(body));
    });
});

server.listen(0, () => {
    const address = server.address();

    if (typeof address === "string") {
        throw new Error();
    }
    process.stdout.write(`RENDERER:${address.port.toString()}:LISTENING`);

    // TODO: load this from a passed in parameter.
    const warmUpTemplate = "HomePage";
    const templatePath = `${process.cwd()}/client/templates/${warmUpTemplate}`;
    require(templatePath);
});
