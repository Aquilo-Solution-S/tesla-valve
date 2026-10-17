// expect: flag-parameter: parameter 'express' seems to be a control flag
package bad

func ShippingDays(express bool) uint {
	if express {
		return 1
	}
	return 3
}
