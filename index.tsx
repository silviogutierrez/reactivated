import React from 'react';
import axios from 'axios';
import express from 'express';
import ReactDOMServer from 'react-dom/server';

const app = express();

app.get('/', async (req, res) => {
    const response = await axios.get('http://localhost:8000/form/');

    if (req.query.raw) {
        res.send(response.data);
    }
    else {
        const {template_name, props} = response.data;
        const Template = require(`./templates/${template_name}.tsx`).default;
        const rendered = ReactDOMServer.renderToString(<Template {...props} />);
        res.send(rendered);
    }

});

app.listen(3000, () => console.log('Example app listening on port 3000!'));
