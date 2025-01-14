import express from "express";
import path from "node:path";
import http from "node:http";
import os from "node:os";
import {SSRErrorResponse, serializeError} from "./errors.js";
import {render} from "./render.mjs";

const socketPath = path.join(os.tmpdir(), `reactivated.${process.pid}.sock`);

const app = express();

app.use(express.json({limit: "200mb"}));
app.use("/_reactivated/", async (req, res) => {
    try {
        render(req, res, "", "production", "index");
    } catch (error) {
        const errResp: SSRErrorResponse = {
            error: serializeError(error as any),
        };
        res.status(500).json(errResp);
    }
});

const server = http.createServer(app);
server.listen(socketPath, () => {
    process.stdout.write(`RENDERER:${socketPath}:LISTENING`);
});

process.on("SIGTERM", () => {
    server.close();
});
