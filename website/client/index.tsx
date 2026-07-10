import {reactivate} from "@reactivated";

import "./styles.css";

// Don't hydrate: react-syntax-highlighter markup diverges in production
// builds. Styles still load through the entry; SSR markup stands alone.
// See: https://github.com/react-syntax-highlighter/react-syntax-highlighter/issues/513
reactivate({
    mount() {
        // Intentionally mounts nothing.
    },
});
