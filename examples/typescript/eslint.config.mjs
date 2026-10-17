import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

const clock = "read the clock at the spring and pass it in";
const flag = "a boolean parameter is a flag: name the choice instead";

export default defineConfig(
  { ignores: ["dist/", "eslint.config.mjs"] },
  tseslint.configs.strictTypeChecked,
  {
    languageOptions: { parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname } },
    rules: {
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "never" }],
      "no-restricted-properties": ["error", { object: "Date", property: "now", message: clock }],
      "no-restricted-syntax": [
        "error",
        { selector: "NewExpression[callee.name='Date'][arguments.length=0]", message: clock },
        { selector: ":function > Identifier[typeAnnotation.typeAnnotation.type='TSBooleanKeyword']", message: flag },
        { selector: ":function > AssignmentPattern[right.raw=/^(true|false)$/]", message: flag },
      ],
    },
  },
  {
    files: ["src/**/*.test.ts"],
    rules: {
      "@typescript-eslint/no-floating-promises": [
        "error",
        { allowForKnownSafeCalls: [{ from: "package", package: "node:test", name: "test" }] },
      ],
    },
  },
);
