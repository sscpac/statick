import eslintConfigPrettier from "eslint-config-prettier";
import html from "eslint-plugin-html";
import js from "@eslint/js";
import prettierPlugin from 'eslint-plugin-prettier';

export default [
    js.configs.recommended,
    eslintConfigPrettier,
    {
        files: ["**/*.html", "**/*.js"],
        plugins: { html, prettier: prettierPlugin },
        rules: {
            "camelcase": "warn",
            "no-console": "off",
        }
    }
];

