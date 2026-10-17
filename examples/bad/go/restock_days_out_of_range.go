// expect: as uint16 value in struct literal (overflows)
package bad

import "example.com/shop"

func Backorder() shop.Stock {
	return shop.Backorder{RestockDays: 70000}
}
