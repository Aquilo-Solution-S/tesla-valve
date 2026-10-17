// region: clock
/** The clock is a spring: read it here, once, and pass the date in. */
export function today(): Date {
  // eslint-disable-next-line no-restricted-syntax -- the one place that reads the clock
  return new Date();
}
// endregion
