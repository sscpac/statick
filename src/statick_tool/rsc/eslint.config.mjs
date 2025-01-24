import html from "eslint-plugin-html";
import prettier from "eslint-plugin-prettier";
import globals from "globals";
import path from "node:path";
import { fileURLToPath } from "node:url";
import js from "@eslint/js";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const compat = new FlatCompat({
    baseDirectory: __dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all
});

export default [...compat.extends("eslint:recommended", "prettier"), {
    files: ["**/*.js", "**.html"],
    plugins: {
        html,
        prettier,
    },

    languageOptions: {
        globals: {
            ...globals.browser,
        },

        ecmaVersion: 9,
        sourceType: "script",

        parserOptions: {
            ecmaFeatures: {
                jsx: false,
            },
        },
    },

    rules: {
        "no-console": "off",
        camelcase: "warn",
    },
}];
