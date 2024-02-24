import {getServerData} from "@reactivated";

// Just so we get styles when building with vite. But don't hydrate, it causes
// issues in production build with react-syntax-highlighter
// See: https://github.com/react-syntax-highlighter/react-syntax-highlighter/issues/513
getServerData();
