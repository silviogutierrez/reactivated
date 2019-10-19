import express, {Request, Response} from "express";

import {BODY_SIZE_LIMIT, render} from "./server";

const app = express();
app.use(express.json({limit: BODY_SIZE_LIMIT}));

app.post("/__ssr/", (req, res) => {
    const rendered = render(Buffer.from(JSON.stringify(req.body)));
    res.json({rendered});
});

const PORT = 1987;

app.listen(PORT, () => {
    // tslint:disable-next-line
    console.log(`Listening on ${PORT}`);
});
