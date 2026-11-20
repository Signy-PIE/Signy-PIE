import js from "@eslint/js"
import globals from "globals"
import tseslint from "typescript-eslint"
import vuePlugin from "eslint-plugin-vue"
import vueParser from "vue-eslint-parser"
import prettier from "eslint-config-prettier"

export default [
  {
    ignores: [
      "**/dist/**",
      "**/build/**",
      "**/coverage/**",
      "**/node_modules/**",
      "**/.venv/**",
      "frontend/public/mediapipe/**",
    ],
  },

  js.configs.recommended,

  ...tseslint.configs.recommended,

  ...vuePlugin.configs["flat/recommended"],

  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tseslint.parser,
    },
  },

  {
    files: ["**/*.vue"],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        parser: tseslint.parser,
        extraFileExtensions: [".vue"],
      },
      globals: {
        ...globals.browser,
      },
    },
  },

  {
    files: ["frontend/**/*.{js,ts,tsx,vue}"],
    languageOptions: {
      globals: {
        ...globals.browser,
      },
    },
  },

  {
    files: ["backend/**/*.{js,ts}", "frontend/vite.config.ts", "eslint.config.js"],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },

  {
    files: ["**/*.{js,mjs,cjs,ts,tsx,vue}"],
    rules: {
      "no-console": "warn",
    },
  },
  prettier,
]
