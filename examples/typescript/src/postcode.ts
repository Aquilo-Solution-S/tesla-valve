export type Invalid = { readonly invalid: string };

// region: postcode
export class Postcode {
  private constructor(readonly code: string) {}

  static parse(raw: string): Postcode | Invalid {
    const code = raw.trim();
    return /^\d{5}$/.test(code)
      ? new Postcode(code)
      : { invalid: "a postcode is five digits" };
  }
}
// endregion
