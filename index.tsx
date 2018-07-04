import React from 'react';
import axios from 'axios';
import express from 'express';

const app = express();
const ReactDOMServer = require('react-dom/server');

app.get('/', async (req, res) => {
    const response = await axios.get('http://localhost:8000/test/');
    console.log(response.data);
    const rendered = ReactDOMServer.renderToString(<div>
        <pre>{JSON.stringify(response.data, null, 2)}</pre>
    </div>);
    res.send(rendered);
});

app.listen(3000, () => console.log('Example app listening on port 3000!'));
