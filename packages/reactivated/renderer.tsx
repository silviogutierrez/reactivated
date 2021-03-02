import express, {Request, Response} from "express";

import {BODY_SIZE_LIMIT, render} from "./server";

const OK_RESPONSE = 200;

// const app = express();
// app.use(express.json({limit: BODY_SIZE_LIMIT}));
//
// app.post("/", (req, res) => {
//     const rendered = render(Buffer.from(JSON.stringify(req.body)));
//     res.json({rendered});
// });
//
// const PORT = 3001;
//
// app.listen(PORT, () => {
//     // tslint:disable-next-line
//     console.log(`Listening on ${PORT}`);
// });

import process from "process";

/*
process.stdin.resume();

let body = Buffer.from(""); // , 'utf8');

process.stdin.on("data", (data) => {
    body = Buffer.concat([body, data as Buffer]);
});
process.stdin.on("end", () => {
    // console.log(`Done with body${body.toString()}ok${body.length}length`);
    // if (body.length > 0) {
        const rendered = render(body);
        process.stdout.write(rendered);
    // }

    body = Buffer.from(""); // , 'utf8');
})
*/

import http from "http";

const server = http.createServer((req, res) => {
    // `req` is an http.IncomingMessage, which is a readable stream.
    // `res` is an http.ServerResponse, which is a writable stream.

    let body = Buffer.from(""); // , 'utf8');
    // Get the data as utf8 strings.
    // If an encoding is not set, Buffer objects will be received.
    // req.setEncoding('utf8');

    // Readable streams emit 'data' events once a listener is added.
    req.on("data", (chunk) => {
        body = Buffer.concat([body, chunk as Buffer]);
    });

    // The 'end' event indicates that the entire body has been received.
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
    // render(Buffer.from(JSON.stringify(fakeRender)));
    const templatePath = `${process.cwd()}/client/templates/${
        fakeRender.context.template_name
    }`;
    // require(templatePath);
    // process.stdout.write("Done requiring");
});

const fakeRender = {
    context: {
        template_name: "BusinessPage",
    },
};
