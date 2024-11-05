import path from "node:path";
import {fileURLToPath} from "node:url";

import {fixupConfigRules} from "@eslint/compat";
import {FlatCompat} from "@eslint/eslintrc";
import eslint from "@eslint/js";
import eslintConfigPrettier from "eslint-config-prettier";
import unusedImports from "eslint-plugin-unused-imports";
import tseslint from "typescript-eslint";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: eslint.configs.recommended,
    allConfig: eslint.configs.all,
});

export default tseslint.config(
    eslint.configs.recommended,
    ...tseslint.configs.recommendedTypeChecked,
    eslintConfigPrettier,
    ...fixupConfigRules(
        compat.extends(
            "plugin:react/recommended",
            "plugin:react-hooks/recommended",
            "plugin:import/typescript",
            "plugin:import/errors",
            "plugin:import/warnings",
        ),
    ),
    {
        plugins: {
            "unused-imports": unusedImports,
        },

        settings: {
            react: {
                version: "detect",
            },

            "import/resolver": "typescript",
        },

        rules: {
            "sort-imports": [
                "error",
                {
                    ignoreDeclarationSort: true,
                },
            ],

            // TypeScript handles this for us.
            "import/namespace": 0,
            "import/named": 0,
            "import/no-unresolved": 0,

            // immer's default export is produce, not matching the filename.
            // TODO: I think immer can be specifically imported now.
            "import/no-named-as-default": 0,
            "import/no-named-as-default-member": 0,

            "import/newline-after-import": ["error"],
            "import/first": ["error"],

            "import/order": [
                "error",
                {
                    alphabetize: {
                        order: "asc",
                    },

                    "newlines-between": "always",

                    pathGroups: [
                        {
                            group: "builtin",
                            pattern: "{react,react-dom}",
                            position: "before",
                        },
                        {
                            group: "builtin",
                            pattern: "{@reactivated,react-*}",
                            position: "after",
                        },
                        {
                            group: "internal",
                            pattern: "@client/actions/*",
                            position: "before",
                        },
                        {
                            group: "internal",
                            pattern:
                                "@client/{app/graphics,shared/analytics,dates,utils,routes,models,style,shared/typography,constants}",
                            position: "before",
                        },
                    ],

                    groups: [
                        "builtin",
                        "external",
                        "internal",
                        "parent",
                        "sibling",
                        "index",
                    ],
                    pathGroupsExcludedImportTypes: ["builtin"],
                },
            ],
            // React overrides
            "react/prop-types": "off",
            // We create way too many components dynamically.
            "react/display-name": "off",
            // We use empty arrays to run once, etc.
            "react-hooks/exhaustive-deps": "off",

            // Typescript overrides from recommended
            "@typescript-eslint/no-unused-vars": "off",
            "unused-imports/no-unused-imports": "error",
            "unused-imports/no-unused-vars": "error",
            "@typescript-eslint/explicit-module-boundary-types": "off",
            "@typescript-eslint/no-non-null-assertion": "off",

            // For when we do RPC calls and forget to call await on the promise
            // to check against a null return.
            "@typescript-eslint/no-unnecessary-condition": "error",

            // We use empty callbacks that are no-ops sometimes.
            "@typescript-eslint/no-empty-function": [
                "error",
                {
                    allow: ["arrowFunctions"],
                },
            ],

            // Typescript additions
            "@typescript-eslint/strict-boolean-expressions": "error",

            // See: https://github.com/typescript-eslint/typescript-eslint/issues/4619#issuecomment-1057096238
            // We want async callbacks to React event handlers
            "@typescript-eslint/no-misused-promises": [
                "error",
                {
                    checksVoidReturn: {
                        attributes: false,
                    },
                },
            ],

            // https://www.reddit.com/r/typescript/comments/uiil9k/am_i_crazy_for_expecting_typescript_to_catch_this/
            "@typescript-eslint/no-use-before-define": ["error"],
        },
    },
);
