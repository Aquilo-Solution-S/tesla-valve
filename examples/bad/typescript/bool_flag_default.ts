// expect: a boolean parameter is a flag
export function shippingDays(express = false): number {
  return express ? 1 : 3;
}
