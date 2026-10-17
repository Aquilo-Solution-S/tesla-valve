// expect: a boolean parameter is a flag
export function shippingDays(express: boolean): number {
  return express ? 1 : 3;
}
