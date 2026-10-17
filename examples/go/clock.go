package shop

import "time"

// region: clock
// Today reads the clock. It is a spring: read it here, once, and pass the date in.
func Today() time.Time {
	return time.Now() //nolint:forbidigo // the one place that reads the clock
}

// endregion
