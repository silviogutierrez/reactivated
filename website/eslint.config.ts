import path from "node:path";
import {fileURLToPath} from "node:url";

import reactivatedConfig from "reactivated/dist/eslint.config";

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
];
