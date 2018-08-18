import React from 'react';

import * as models from './models';

export const {Provider, Consumer} = React.createContext({
    request: {
        path: '',
    },
    template_name: '',
    csrf_token: '',
    messages: [] as models.Message[],
});
