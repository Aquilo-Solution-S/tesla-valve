// expect: no-explicit-any
export function passthrough(value: any): unknown {
  return value;
}
