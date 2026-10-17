// expect: cannot refer to unexported field code
package bad

import "example.com/shop"

func Forged() shop.Postcode {
	return shop.Postcode{code: "hello"}
}
