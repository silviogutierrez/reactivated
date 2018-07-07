import React from 'react';
import {hydrate} from 'react-dom';
import FormView from './templates/FormView';


const props = (window as any).__PRELOADED_STATE__;
const CastedFormView = FormView as any;

hydrate(<CastedFormView {...props} />, document.getElementById('root'));
