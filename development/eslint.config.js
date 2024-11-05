import path from "node:path";
import {fileURLToPath} from "node:url";

import reactivatedConfig from "reactivated/dist/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default [
    ...reactivatedConfig,
    {
        languageOptions: {
            parserOptions: {
                project: ["./tsconfig.json"],
                projectService: true,
                tsconfigRootDir: __dirname,
            },
        },
    },
    {
        ignores: [
            "eslint.config.js",
            ".venv/**/*",
            "**/*/*.pyc",
            "**/.DS_Store",
            ".mypy_cache",
            ".pytest_cache",
            "static/dist/**/*",
        ],
    },
];
