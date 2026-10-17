// expect: shop.Backorder is missing field RestockDays
package bad

import "example.com/shop"

func Backorder() shop.Stock {
	return shop.Backorder{}
}
