import React from 'react';
import fs from 'fs';
import ReactDOMServer from 'react-dom/server';
import {render} from './server';

const stdinBuffer = fs.readFileSync(0); // STDIN_FILENO = 0

process.stdout.write(render(stdinBuffer));
