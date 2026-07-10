import path from "path";

import type {Plugin} from "vite";

export const VIRTUAL_TEMPLATES = "virtual:reactivated/templates";
export const VIRTUAL_ENTRY = "virtual:reactivated/entry";

const templatesModule = `
const templates = import.meta.glob("/client/templates/*.tsx", {eager: true});

export const getTemplate = async ({template_name}) => {
    const templatePath = "/client/templates/" + template_name + ".tsx";
    const templateModule = templates[templatePath];

    if (templateModule == null) {
        throw new Error(
            "reactivated: no template found at " + templatePath +
            " — every Template class needs a matching .tsx file exporting {Template}",
        );
    }
    return templateModule.Template;
};
`;

const entryModule = `
// The default reactivated entry.
//
// Your app is running without a client/index.tsx — this virtual module is
// standing in for it. To customize startup, create client/index.tsx:
//
//     import {reactivate} from "@reactivated";
//
//     reactivate({
//         async init({context, props}) {
//             // browser-only setup; awaited before hydration
//         },
//         render: (content, {ssr}) => content, // wrap with providers
//     });
//
// The file wins over this default as soon as it exists.
import {reactivate} from "reactivated/dist/client";

reactivate();
`;

export const reactivated = (): Plugin => ({
    name: "reactivated",
    resolveId(id) {
        if (id === VIRTUAL_TEMPLATES || id === VIRTUAL_ENTRY) {
            return id;
        }
        return null;
    },
    load(id) {
        if (id === VIRTUAL_TEMPLATES) {
            return templatesModule;
        }
        if (id === VIRTUAL_ENTRY) {
            return entryModule;
        }
        return null;
    },
});

/**
 * The reactivated config surface, in one place: the plugin plus the
 * aliases every pipeline needs (dev server, build, and any vite-family
 * tooling like vitest). Spread it instead of hand-copying aliases.
 */
export const preset = () => ({
    plugins: [reactivated()],
    resolve: {
        // The package is often consumed via a file: symlink (vendored
        // subtree); its dist files would otherwise resolve react from the
        // subtree's own node_modules — two React copies in one bundle is a
        // null-dispatcher crash at SSR time. dedupe (not an absolute-path
        // alias) collapses them to the app's copy: an abs-path alias forces
        // vite to inline react, and inlining its CommonJS entry breaks SSR
        // ("module is not defined"); dedupe keeps react externalizable.
        dedupe: ["react", "react-dom"],
        // Array form: bare "@reactivated" is the generated index, while
        // "@reactivated/icons" etc. map into client/generated/.
        alias: [
            {
                find: /^@reactivated$/,
                replacement: path.resolve(
                    process.cwd(),
                    "./client/generated/index.tsx",
                ),
            },
            {
                find: "@reactivated",
                replacement: path.resolve(process.cwd(), "./client/generated"),
            },
            {find: "@client", replacement: path.resolve(process.cwd(), "./client")},
        ],
    },
});
