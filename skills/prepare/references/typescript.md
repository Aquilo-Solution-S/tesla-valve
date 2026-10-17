# TypeScript

| tool | holds | comes with |
| --- | --- | --- |
| `tsc`, `strict` | every type, private constructors, brands, `never` in `unreachable` | a dev dependency |
| ESLint with typescript-eslint | every case of a `switch`, no `as`, no `any`, no `boolean` parameter, no clock inside the logic | dev dependencies |
| zod | the closed choice and the range at the spring, while the code runs | a dependency of the code |

## The tools

All of them are packages, pinned in the lockfile and installed in CI with
`npm ci --ignore-scripts`, which runs no package's install script.
typescript-eslint supports a range of TypeScript versions: pin TypeScript
inside it.

<!-- code: examples/typescript/package.json -->
```json
{
  "name": "shop",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "tsc && node --test \"dist/**/*.test.js\""
  },
  "dependencies": {
    "zod": "4.6.5"
  },
  "devDependencies": {
    "@types/node": "24.19.1",
    "eslint": "10.12.0",
    "typescript": "6.0.3",
    "typescript-eslint": "8.71.1"
  }
}
```

## The configs

In `tsconfig.json`. The first three options are the enforcers; the rest is the
example's build:

<!-- code: examples/typescript/tsconfig.json -->
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "target": "es2024",
    "module": "nodenext",
    "rootDir": "src",
    "outDir": "dist",
    "types": ["node"]
  },
  "include": ["src"]
}
```

In `eslint.config.mjs`:

<!-- code: examples/typescript/eslint.config.mjs -->
```js
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
```

`strictTypeChecked` brings `no-explicit-any` and `no-unsafe-assignment`, and
`projectService` gives the rules the types they read. The config itself is not
part of the TypeScript project, so it is ignored, and `node:test`'s `test` is
allowed to float its promise.

The clock ban finds every place the project reads the clock today. They move
behind one function, the way
[the clock](../../tesla-valve/references/typescript.md#the-clock) shows.

## CI

```sh
npm ci --ignore-scripts
npx tsc --noEmit
npx eslint .
npm test
```

## The proofs

Run `npx tsc --noEmit` and `npx eslint .` in the copy. Put the bad file inside
the TypeScript project, such as `src/bad.ts`, so the rules that read types see
it.

The compiler refuses a forged value and a plain number for a brand:

<!-- code: examples/bad/typescript/forged_postcode.ts -->
```ts
// expect: error TS2673
import { Postcode } from "./postcode.js";

export const forged = new Postcode("hello");
```

<!-- code: examples/bad/typescript/unbranded_restock_days.ts -->
```ts
// expect: error TS2322
import type { Stock } from "./delivery.js";

export const backorder: Stock = { status: "backorder", restock_days: -3 };
```

Both refuse a missing case:

<!-- code: examples/bad/typescript/missing_case.ts -->
```ts
// expect: switch-exhaustiveness-check
// expect: error TS2345
import type { Stock } from "./delivery.js";
import { unreachable } from "./unreachable.js";

export function restockDays(stock: Stock): number {
  switch (stock.status) {
    case "in_stock":
      return 0;
    default:
      return unreachable(stock);
  }
}
```

ESLint refuses the leaks, a boolean flag and the clock:

<!-- code: examples/bad/typescript/cast_forges_a_value.ts -->
```ts
// expect: consistent-type-assertions
import type { Stock } from "./delivery.js";

export function forged(raw: string): Stock {
  return JSON.parse(raw) as Stock;
}
```

<!-- code: examples/bad/typescript/any_annotation.ts -->
```ts
// expect: no-explicit-any
export function passthrough(value: any): unknown {
  return value;
}
```

<!-- code: examples/bad/typescript/bool_flag.ts -->
```ts
// expect: a boolean parameter is a flag
export function shippingDays(express: boolean): number {
  return express ? 1 : 3;
}
```

<!-- code: examples/bad/typescript/bool_flag_default.ts -->
```ts
// expect: a boolean parameter is a flag
export function shippingDays(express = false): number {
  return express ? 1 : 3;
}
```

<!-- code: examples/bad/typescript/clock_date_now.ts -->
```ts
// expect: no-restricted-properties
export function now(): number {
  return Date.now();
}
```

<!-- code: examples/bad/typescript/clock_new_date.ts -->
```ts
// expect: no-restricted-syntax
export function today(): Date {
  return new Date();
}
```
