import http from "http";
import ReactDOMServer from "react-dom/server";
import React from "react";

import templates, {filenames} from './templates/**/*';

console.log(templates, filenames);

const OK_RESPONSE = 200;

const ERROR_REPONSE = 500;

const PORT = 3000;

type Rendered = {
    status: "success",
    rendered: string;
} | {
    status: "error",
    error: unknown,
}

const render = (url: string, body: Buffer): Rendered => {
    const templatePath = url.includes("Page") ? "./templates/Page.tsx" : "./templates/Login.tsx";
    const Template = templates.find((t, index) => filenames[index] === templatePath).default;
    // const Component = require("./templates/Page").default;
    // const Component = require(templatePath).default;
    const Component = Template;

    const rendered = ReactDOMServer.renderToString(
        <Component />
    );

    return {
        status: "success",
        rendered,
    }
}

const server = http.createServer((req, res) => {
    let body = Buffer.from("");

    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });
    req.on("end", () => {
        const result = render(req.url, body);

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

server.listen(PORT, () => {
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
