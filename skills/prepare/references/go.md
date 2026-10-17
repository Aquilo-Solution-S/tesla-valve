# Go

| tool | holds | comes with |
| --- | --- | --- |
| the compiler | every type, unexported fields outside their package, a constant inside its type | Go |
| `exhaustive` | every constant of a named type in a `switch` | golangci-lint |
| `gochecksumtype` | every variant of an interface marked `//sumtype:decl` in a type switch | golangci-lint |
| `exhaustruct_v5` | every field in a struct literal | golangci-lint |
| `forbidigo` | no clock inside the logic | golangci-lint |
| revive's `flag-parameter` | no `bool` parameter the function branches on | golangci-lint |

## The tools

The compiler, `go vet` and `go test` come with Go. golangci-lint is one binary
that runs many linters. Pin its version wherever it is installed:

<!-- code: .github/workflows/test.yml#golangci-lint -->
```sh
go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.14.0
```

The config below is for v2. A project with a v1 config, one without
`version: "2"`, converts it first with `golangci-lint migrate`.

## The config

In `.golangci.yml`:

<!-- code: examples/go/.golangci.yml -->
```yaml
version: "2"
linters:
  enable:
    - exhaustive
    - gochecksumtype
    - exhaustruct_v5
    - forbidigo
    - revive
  settings:
    exhaustive:
      default-signifies-exhaustive: false
    gochecksumtype:
      default-signifies-exhaustive: false
    forbidigo:
      analyze-types: true
      forbid:
        - pattern: ^time\.(Now|Since|Until)$
          msg: read the clock at the spring and pass it in
    revive:
      rules:
        - name: flag-parameter
```

`default-signifies-exhaustive: false` is the point of both settings: with
`true`, a `default` counts as every missing case. `analyze-types` catches the
clock under a renamed import too.

A `rules` list replaces revive's default rules. In a project that runs revive on
its defaults, add `enable-default-rules: true` beside the list, or the merge
drops them.

`exhaustruct_v5` asks every struct literal to set every field, the standard
library's included, so on existing code it usually finds the most.

The clock ban finds every place the project reads the clock today. They move
behind one function, the way
[the clock](../../tesla-valve/references/go.md#the-clock) shows.

## CI

```sh
go vet ./...
go test ./...
golangci-lint run ./...
```

## The proofs

Run `golangci-lint run ./...` in the copy; it reports compile errors too. Put
the bad file in a package of its own, such as `bad/bad.go`, so it uses the
project's package from outside, where unexported fields are private.

The compiler refuses a forged value and a constant out of range:

<!-- code: examples/bad/go/forged_postcode.go -->
```go
// expect: cannot refer to unexported field code
package bad

import "example.com/shop"

func Forged() shop.Postcode {
	return shop.Postcode{code: "hello"}
}
```

<!-- code: examples/bad/go/restock_days_out_of_range.go -->
```go
// expect: as uint16 value in struct literal (overflows)
package bad

import "example.com/shop"

func Backorder() shop.Stock {
	return shop.Backorder{RestockDays: 70000}
}
```

`gochecksumtype` refuses a missing variant, with a `default` or without:

<!-- code: examples/bad/go/missing_case.go -->
```go
// expect: missing cases for Backorder
package bad

import "example.com/shop"

func RestockDays(stock shop.Stock) uint16 {
	switch stock.(type) {
	case shop.InStock:
		return 0
	}
	return 0
}
```

<!-- code: examples/bad/go/default_hides_a_case.go -->
```go
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
```

`exhaustive` refuses a missing constant:

<!-- code: examples/bad/go/weekday_missing_case.go -->
```go
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
```

`exhaustruct_v5` refuses a variant without its data:

<!-- code: examples/bad/go/backorder_without_days.go -->
```go
// expect: shop.Backorder is missing field RestockDays
package bad

import "example.com/shop"

func Backorder() shop.Stock {
	return shop.Backorder{}
}
```

revive refuses a `bool` the function branches on:

<!-- code: examples/bad/go/bool_flag.go -->
```go
// expect: flag-parameter: parameter 'express' seems to be a control flag
package bad

func ShippingDays(express bool) uint {
	if express {
		return 1
	}
	return 3
}
```

`forbidigo` refuses the clock, also under another name:

<!-- code: examples/bad/go/clock_now.go -->
```go
// expect: use of `time.Now` forbidden
package bad

import "time"

func Today() time.Time {
	return time.Now()
}
```

<!-- code: examples/bad/go/clock_since.go -->
```go
// expect: use of `time.Since` forbidden
package bad

import "time"

func Age(born time.Time) time.Duration {
	return time.Since(born)
}
```

<!-- code: examples/bad/go/clock_renamed.go -->
```go
// expect: use of `clock.Now` forbidden
package bad

import clock "time"

func Today() clock.Time {
	return clock.Now()
}
```
