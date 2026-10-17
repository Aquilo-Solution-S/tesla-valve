// expect: use of `clock.Now` forbidden
package bad

import clock "time"

func Today() clock.Time {
	return clock.Now()
}
