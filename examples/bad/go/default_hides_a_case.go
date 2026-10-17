// expect: missing cases for Backorder
package bad

import "example.com/shop"

func RestockDays(stock shop.Stock) uint16 {
	switch stock.(type) {
	case shop.InStock:
		return 0
	default:
		return 0
	}
}
