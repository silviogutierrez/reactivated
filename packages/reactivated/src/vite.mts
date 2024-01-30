import express from "express";
import path from "path";

import {renderPage} from "./renderer";
import {vanillaExtractPlugin} from "@vanilla-extract/vite-plugin";

const isProduction = process.env.NODE_ENV === "production";
const port = process.env.PORT || 5173;
const base = process.env.BASE || "/";

const app = express();

const indexHTML = `
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React + TS</title>
    <!--app-head-->
  </head>
  <body>
    <div id="root"><!--app-html--></div>
    <script type="module" src="/client/entry-client.tsx"></script>
  </body>
</html>
`;

const {createServer} = await import("vite");

const vite = await createServer({
    server: {middlewareMode: true, proxy: {
        /*
        "^.*": {
            target: "http://main.joyapp.com.silviogutierrez.localhost:12008/",
        },
        */
    }},
    appType: "custom",
    plugins: [vanillaExtractPlugin()],
    resolve: {
        alias: {
             "@client": path.resolve(process.cwd(), "./client"),
             "@reactivated": path.resolve(process.cwd(), "./node_modules/_reactivated"),
        },
    },
    base,
});

app.use(vite.middlewares);

app.use("*", async (req, res) => {
    const templateName = req.query.templateName ?? "HelloWorld";

    const url = "";
    const template = await vite.transformIndexHtml(url, indexHTML);
    const render = (await vite.ssrLoadModule("/client/entry-server.tsx")).render;

    const ssrManifest = null;
    // const rendered = await render(url, ssrManifest)
    const rendered = await render(templateName);

    const html = template
        .replace(`<!--app-head-->`, rendered.head ?? "")
        .replace(`<!--app-html-->`, rendered.html ?? "");

    res.status(200).set({"Content-Type": "text/html"}).end(html);
});

app.listen(port, () => {
    console.log(`Server started at http://localhost:${port}`);
});
