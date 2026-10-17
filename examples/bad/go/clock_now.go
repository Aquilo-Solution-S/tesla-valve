// expect: use of `time.Now` forbidden
package bad

import "time"

func Today() time.Time {
	return time.Now()
}
