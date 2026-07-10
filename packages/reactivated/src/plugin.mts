import path from "path";

import type {Plugin} from "vite";

export const VIRTUAL_TEMPLATES = "virtual:reactivated/templates";
export const VIRTUAL_ENTRY = "virtual:reactivated/entry";

// reactivate/reactivateAdmin are declared ambient in the generated @reactivated
// index (see generator.mts) so they never become a value import from that shared
// module. The transform below re-homes their runtime to the framework client,
// but only in the module actually importing them (the entry) - keeping the
// framework client out of the graph shared by every app module, which is what
// forms the react-refresh cycle.
//
// Alternative if this rewrite ever gets too gnarly (odd import syntaxes, build
// interactions, sourcemaps): emit reactivate/reactivateAdmin into a SEPARATE
// generated module `@reactivated/client` (client/generated/client.tsx) that only
// the entry imports, and drop this transform + the ambient declares. Consumers
// then write `import {reactivate} from "@reactivated/client"` instead of the
// single `@reactivated`. Fully worked out and verified in the (closed) sibling
// PR; the only cost there is the extra import path in each entry.
const RUNTIME_NAMES = new Set(["reactivate", "reactivateAdmin"]);
const RUNTIME_SOURCE = "reactivated/dist/client";

// Matches: import { ...names... } from "@reactivated";  (quotes/semicolon/ws tolerant)
const REACTIVATED_IMPORT = /import\s*\{([^}]*)\}\s*from\s*["']@reactivated["']\s*;?/g;

const splitSpecifiers = (clause: string): string[] =>
    clause
        .split(",")
        .map((specifier) => specifier.trim())
        .filter(Boolean);

// The source-facing name of a specifier: for "x as y" that is "x".
const importedName = (specifier: string): string =>
    specifier.split(/\s+as\s+/)[0].trim();

const rewriteReactivatedImports = (code: string): string | null => {
    let changed = false;
    const out = code.replace(REACTIVATED_IMPORT, (full, clause: string) => {
        const specifiers = splitSpecifiers(clause);
        const runtime = specifiers.filter((s) => RUNTIME_NAMES.has(importedName(s)));
        if (runtime.length === 0) {
            return full;
        }
        changed = true;
        const rest = specifiers.filter((s) => !RUNTIME_NAMES.has(importedName(s)));
        const lines = [`import {${runtime.join(", ")}} from "${RUNTIME_SOURCE}";`];
        if (rest.length > 0) {
            lines.push(`import {${rest.join(", ")}} from "@reactivated";`);
        }
        return lines.join("\n");
    });
    return changed ? out : null;
};

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
    // Re-home runtime reactivate/reactivateAdmin from @reactivated to the
    // framework client. Runs in dev AND build (no apply guard); returning null
    // when nothing changed leaves sourcemaps untouched.
    transform(code, id) {
        const [file] = id.split("?");
        if (!/\.[cm]?[jt]sx?$/.test(file)) {
            return null;
        }
        if (!code.includes("@reactivated")) {
            return null;
        }
        const rewritten = rewriteReactivatedImports(code);
        if (rewritten == null) {
            return null;
        }
        return {code: rewritten, map: null};
    },
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
