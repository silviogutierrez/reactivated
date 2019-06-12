import React from 'react';
import fs from 'fs';
import ReactDOMServer from 'react-dom/server';

const stdinBuffer = fs.readFileSync(0); // STDIN_FILENO = 0

const props = JSON.parse(stdinBuffer.toString());
const template_path = `${process.cwd()}/client/templates/${props.template_name}.tsx`;

const Template = require(template_path).Template;
const rendered = ReactDOMServer.renderToString(<Template {...props} />);
process.stdout.write(rendered);
