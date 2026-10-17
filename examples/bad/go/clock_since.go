// expect: use of `time.Since` forbidden
package bad

import "time"

func Age(born time.Time) time.Duration {
	return time.Since(born)
}
