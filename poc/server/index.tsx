import {render} from "reactivated/server";
import fs from "fs";

const REACTIVATED_CLIENT_ROOT = process.env.REACTIVATED_CLIENT_ROOT ?? `./client`;

import * as templates from '../client/templates/**/*';
import {Provider} from "@client/generated";
const stdinBuffer = fs.readFileSync(0);
process.stdout.write(JSON.stringify(render(Provider, templates, stdinBuffer)));
