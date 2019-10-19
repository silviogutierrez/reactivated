import fs from "fs";
import React from "react";
import ReactDOMServer from "react-dom/server";
import {render} from "./server";

const stdinBuffer = fs.readFileSync(0); // STDIN_FILENO = 0

process.stdout.write(render(stdinBuffer));
