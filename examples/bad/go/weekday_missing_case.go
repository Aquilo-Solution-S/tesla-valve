// expect: missing cases in switch of type time.Weekday
package bad

import "time"

func Weekend(day time.Weekday) bool {
	switch day {
	case time.Saturday, time.Sunday:
		return true
	case time.Monday, time.Tuesday, time.Wednesday, time.Thursday:
		return false
	}
	return false
}
