// expect: error TS2673
import { Postcode } from "./postcode.js";

export const forged = new Postcode("hello");
