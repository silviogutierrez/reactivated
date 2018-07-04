import React from 'react';
import axios from 'axios';
import * as express from 'express';

const app = express();
const ReactDOMServer = require('react-dom/server');

app.get('/', async (req, res) => {
    const response = await axios.get('https://www.google.com');
    console.log(response.data);
    const rendered = ReactDOMServer.renderToString(<div>Hello!</div>);
    res.send(rendered);
});

app.listen(3000, () => console.log('Example app listening on port 3000!'));
