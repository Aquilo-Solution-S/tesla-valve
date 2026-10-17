// region: unreachable
/**
 * Proves at compile time that every case is handled, and fails loudly when
 * data the types never allowed arrives anyway.
 */
export function unreachable(value: never): never {
  throw new Error(`unreachable: ${JSON.stringify(value)}`);
}
// endregion
