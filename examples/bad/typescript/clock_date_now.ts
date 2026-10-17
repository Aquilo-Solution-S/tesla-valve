// expect: no-restricted-properties
export function now(): number {
  return Date.now();
}
