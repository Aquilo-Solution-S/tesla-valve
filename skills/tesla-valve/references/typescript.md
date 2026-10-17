# TypeScript

TypeScript is softer ground. Its types are erased when the code runs, `any` and
`as` pass through every wall, and plain types match by shape, not by name. A
channel in soft ground holds only where it is lined, so the lint rules below
are not optional. Wherever the types are gone, at JSON and at any API that
plain JavaScript can call, the runtime check stays.

| wrong shape | right shape | enforcer | not when |
| --- | --- | --- | --- |
| a closed choice as `string`, compared to literals | a discriminated union, every variant a `case`, and `default` calls `unreachable(x: never)` | `switch-exhaustiveness-check`; `unreachable` does not compile while a case is missing | the set is owned elsewhere and can grow: parse it at the spring, with an explicit unknown arm |
| a `boolean` parameter, called as `shippingDays(true)` | a union of string literals that names the choice | `no-restricted-syntax`, for a parameter typed `boolean` or defaulting to `true` or `false` | one two-valued choice in an options object: `{ express: true }` names itself |
| an optional field that must be present in one state | a union variant that carries it | `strict` | the value is optional in every state |
| several `boolean` fields that together encode one state: `paid`, `shipped`, `cancelled` | a discriminated union of the states | review: no rule counts them | the booleans are truly independent |
| `JSON.parse(input) as Shape`, or a validator that returns its input unchanged | parse `unknown` with a schema, such as zod, and return the value or the reason it could not | `no-unsafe-assignment`, `no-explicit-any`, `consistent-type-assertions` set to `never` | a generated client already parsed it: do not parse twice |
| a `number` or `string` that carries a range, a trust property or a checked id | a branded type from a schema's `.brand()`: parsing is the only way in | `strict`: a plain value does not assign to the brand | the value never crosses a trust boundary and has no range |
| a public constructor and a `validate()` to call afterwards | a private constructor and a static `parse` | `private`, at compile time only | the class never crosses a boundary: then a plain type is lighter |
| literals repeated at every call site | one `as const` tuple and the union derived from it | `strict` | the vocabulary belongs to a contract package: import it |
| `Date.now()` or `new Date()` inside the logic | read the clock at the spring and pass the date in | `no-restricted-properties` and `no-restricted-syntax` | the one function that reads it, under `eslint-disable-next-line` with the reason |

## A closed choice, parsed at the spring

The schema is the check, and the type comes from it. `restock_days` is a
branded integer from 0 to 65,535: the warehouse's JSON cannot carry `-3`,
because the schema refuses it, and code cannot build a backorder with `-3`
either, because a plain number does not assign to the brand. The range keeps
the sum an exact integer.

<!-- code: examples/typescript/src/delivery.ts#stock -->
```ts
const RestockDays = z.int().min(0).max(65535).brand<"RestockDays">();

export const Stock = z.discriminatedUnion("status", [
  z.object({ status: z.literal("in_stock") }),
  z.object({ status: z.literal("backorder"), restock_days: RestockDays }),
]);
export type Stock = z.infer<typeof Stock>;

export function deliveryDate(postcode: Postcode, stock: Stock, today: Date): Date {
  const date = new Date(today);
  date.setUTCDate(date.getUTCDate() + days(postcode, stock));
  return date;
}

function days(postcode: Postcode, stock: Stock): number {
  switch (stock.status) {
    case "in_stock":
      return shippingDays(postcode);
    case "backorder":
      return stock.restock_days + shippingDays(postcode);
    default:
      return unreachable(stock);
  }
}
```

`unreachable` takes `never`, so a missing case does not compile. If data the
types never allowed arrives anyway, it throws instead of returning nonsense.
`return x satisfies never` would compile the same, and at runtime return the
stray value as the result.

<!-- code: examples/typescript/src/unreachable.ts#unreachable -->
```ts
/**
 * Proves at compile time that every case is handled, and fails loudly when
 * data the types never allowed arrives anyway.
 */
export function unreachable(value: never): never {
  throw new Error(`unreachable: ${JSON.stringify(value)}`);
}
```

The spring parses `unknown` and returns the value or the reason:

<!-- code: examples/typescript/src/delivery.ts#spring -->
```ts
export function stockOf(json: string): Stock | Invalid {
  let data: unknown;
  try {
    data = JSON.parse(json);
  } catch {
    return { invalid: "the warehouse sent no JSON" };
  }
  const parsed = Stock.safeParse(data);
  return parsed.success ? parsed.data : { invalid: parsed.error.message };
}
```

## One constructor

`private` holds only at compile time. A cast or `JSON.parse` forges a
`Postcode` without `parse`, which is why the lint rules forbid both. A type
guard that lies forges one too:
`(x: unknown): x is Postcode => typeof x === "string"` compiles, and no rule
here refuses it. Keep type guards out of the domain; parse instead.

<!-- code: examples/typescript/src/postcode.ts#postcode -->
```ts
export class Postcode {
  private constructor(readonly code: string) {}

  static parse(raw: string): Postcode | Invalid {
    const code = raw.trim();
    return /^\d{5}$/.test(code)
      ? new Postcode(code)
      : { invalid: "a postcode is five digits" };
  }
}
```

A shape test is one line, `// @ts-expect-error` above the wrong use. It passes
on any error on that line, so keep the line minimal.

## The clock

ESLint refuses the clock everywhere but in the one function that reads it,
which says why it may:

<!-- code: examples/typescript/src/clock.ts#clock -->
```ts
/** The clock is a spring: read it here, once, and pass the date in. */
export function today(): Date {
  // eslint-disable-next-line no-restricted-syntax -- the one place that reads the clock
  return new Date();
}
```

The
[TypeScript example](https://github.com/Aquilo-Solution-S/tesla-valve/tree/main/examples/typescript)
runs every enforcer above, and each is fed a file it must refuse.
