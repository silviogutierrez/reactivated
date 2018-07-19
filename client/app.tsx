import React from 'react';
import {hydrate} from 'react-dom';
import {setStylesTarget} from "typestyle";

import FormView from './templates/FormView';

const props = (window as any).__PRELOADED_STATE__;

const Template = require('./templates/' + props.template_name + '.tsx').default;

hydrate(<Template {...props} />, document.getElementById('root'));
setStylesTarget(document.getElementById('styles-target')!);
