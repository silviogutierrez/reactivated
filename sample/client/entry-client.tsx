import React from 'react'
import ReactDOM from 'react-dom/client'
import {App} from './App'

const templateName = (new URLSearchParams(location.search)).get("templateName") ?? "HelloWorld";
const templates = import.meta.glob("../client/templates/*.tsx", {eager: true});
const Template = templates[`./templates/${templateName}.tsx`].default;


ReactDOM.hydrateRoot(
  document.getElementById('root') as HTMLElement,
  <React.StrictMode>
    <Template />
  </React.StrictMode>
)
