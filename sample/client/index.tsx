import {reactivate} from "@reactivated";

import "./styles.css";

// The minimal customized entry: everything here also works with no entry
// file at all (the virtual default is a bare reactivate() call). This file
// exists to exercise the single-entry contract: it is evaluated during SSR
// too, so its module scope stays node-safe and browser-only setup goes in
// init.
reactivate({
    init() {
        console.log("Browser setup: runs before hydration, never on the server");
    },
    render: (content, {ssr}) => {
        if (ssr) {
            console.log("Rendering on the server");
        }
        return content;
    },
});
