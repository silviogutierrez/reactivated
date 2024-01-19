#!/usr/bin/env node

import fs from "fs";
import path from "path";

import * as esbuild from "esbuild";

const CONF_INPUT_FILE = "./client/reactivated.config.tsx";
const CONF_OUTPUT_FILE = "./node_modules/_reactivated/conf.mjs";

if (fs.existsSync(CONF_INPUT_FILE)) {
    await esbuild.build({
        entryPoints: [CONF_INPUT_FILE],
        bundle: false,
        outfile: CONF_OUTPUT_FILE,
    });
} else {
    fs.mkdirSync(path.dirname(CONF_OUTPUT_FILE), {recursive: true});
    fs.writeFileSync(CONF_OUTPUT_FILE, "");
}
