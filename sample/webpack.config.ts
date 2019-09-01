import {createConfig} from "reactivated/webpack";

const config = createConfig({
    DEBUG_PORT: parseInt(process.env["DEBUG_PORT"]),
    MEDIA_URL: "/media/",
    STATIC_URL: "/static/",
    DEBUG: true,
});

export default {
    ...config,
}
