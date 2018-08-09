import React from 'react';
import {hydrate} from 'react-dom';
import {setStylesTarget} from "typestyle";

const props = (window as any).__PRELOADED_STATE__;

if ((module as any).hot) {
    (module as any).hot.accept()
}

const Template = require('templates/' + props.template_name + '.tsx').default;

hydrate(<Template {...props} />, document.getElementById('root'));

setStylesTarget(document.getElementById('styles-target')!);
