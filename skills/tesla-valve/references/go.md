# Go

Go is firm ground with holes. The compiler checks every type, and an
unexported field is truly private outside its package. But Go has no sum
types, every type has a zero value nobody constructed, and an interface can be
nil. Let golangci-lint close what it can, and know the holes it cannot.

| wrong shape | right shape | enforcer | not when |
| --- | --- | --- | --- |
| a closed choice as `string`, compared to literals | a named type with constants, switched case by case | `exhaustive`, with `default-signifies-exhaustive: false` | the set is owned elsewhere and can grow: parse it at the spring, and refuse what you do not know |
| a closed choice whose variants carry data, as one struct with optional fields | an interface with an unexported method, marked `//sumtype:decl`, one struct per variant; a type switch with every case, and a `default` that panics | `gochecksumtype`, with `default-signifies-exhaustive: false`: the `default` does not count as a case | the variants carry nothing: named constants are lighter |
| a `bool` parameter the function branches on | two functions, or a named type with constants | revive's `flag-parameter` | the bool is data: stored or passed on, never branched on |
| a field that must be set in one state | the variant's struct carries it | `exhaustruct_v5`: a literal sets every field | the field is optional in every state |
| several `bool` fields that together encode one state: `Paid`, `Shipped`, `Cancelled` | an interface marked `//sumtype:decl` with one struct per state, or a named type with constants when no state carries data | review: no linter counts them | the bools are truly independent |
| a count wider than its range, so a sum can overflow | the narrowest integer that holds the range | the decoder refuses a value out of range; a constant out of range does not compile | never |
| exported fields on a value with an invariant | unexported fields, and `ParseX(raw) (X, error)` as the only way in | the compiler: outside the package, unexported fields cannot be set | a value with no invariant stays a primitive |
| `json.Unmarshal` straight into the domain type | decode into a wire struct, pointers for required fields, then parse | the parse function: `encoding/json` fills missing fields with zero values | never |
| `time.Now()` inside the logic | read the clock at the spring and pass it in | `forbidigo`, with `analyze-types`, so a renamed import is caught too | the one function that reads it, under `//nolint:forbidigo` with the reason |

## A closed choice, parsed at the spring

<!-- code: examples/go/shop.go#stock -->
```go
//sumtype:decl
type Stock interface{ isStock() }

type InStock struct{}

type Backorder struct{ RestockDays uint16 }

func (InStock) isStock()   {}
func (Backorder) isStock() {}

// DeliveryDate panics on a Postcode that did not come from ParsePostcode, and
// on a Stock that is none of its variants: both are mistakes in the code, not
// in the data.
func DeliveryDate(postcode Postcode, stock Stock, today time.Time) time.Time {
	if postcode.code == "" {
		panic("a Postcode comes from ParsePostcode")
	}
	var days uint
	switch s := stock.(type) {
	case InStock:
		days = shippingDays(postcode)
	case Backorder:
		days = uint(s.RestockDays) + shippingDays(postcode)
	default:
		panic(fmt.Sprintf("not a Stock: %T", s))
	}
	return today.AddDate(0, 0, int(days))
}
```

`encoding/json` does not refuse anything on its own, so the spring is a parse
function. A pointer tells a missing field from a zero, and `uint16` refuses a
negative count and anything above 65,535, so the sum cannot overflow. A `uint`
would wrap silently into a wrong date.

<!-- code: examples/go/shop.go#spring -->
```go
func StockOf(raw []byte) (Stock, error) {
	var wire struct {
		Status      string  `json:"status"`
		RestockDays *uint16 `json:"restock_days"`
	}
	if err := json.Unmarshal(raw, &wire); err != nil {
		return nil, err
	}
	switch {
	case wire.Status == "in_stock":
		return InStock{}, nil
	case wire.Status == "backorder" && wire.RestockDays != nil:
		return Backorder{RestockDays: *wire.RestockDays}, nil
	}
	return nil, fmt.Errorf("unknown stock: %s", raw)
}
```

## One constructor

<!-- code: examples/go/shop.go#postcode -->
```go
type Postcode struct{ code string }

func ParsePostcode(raw string) (Postcode, error) {
	code := strings.TrimSpace(raw)
	if len(code) != 5 || strings.Trim(code, "0123456789") != "" {
		return Postcode{}, errors.New("a postcode is five digits")
	}
	return Postcode{code: code}, nil
}
```

The unexported field holds the constructor. Go has no test that a line does not
compile, so write none: no test runs the compiler or `go/types` to prove it.

## The holes

The interface is closed by convention, not by the language.

- **A pointer, an embedding and nil.** With value receivers, `&Backorder{}`
  satisfies `Stock` too. So does a struct in another package that embeds
  `shop.Stock`, and so does `nil`. All three compile, pass the linters and match
  no case, which is why the `default` panics instead of returning today.
- **The zero value.** `shop.Postcode{}` compiles outside the package and holds
  an empty code. No linter refuses it, so `DeliveryDate` does.
- **An integer enum takes any integer.** `Kind(42)` compiles. When the value
  comes from outside, parse it at the spring.

Each hole is a mistake in the code, not in the data, so a panic is the right
answer: it fails the first test that walks into it. Data from outside goes
through `StockOf` and `ParsePostcode`, which return errors.

## The clock

`forbidigo` refuses the clock everywhere but in the one function that reads
it, which says why it may:

<!-- code: examples/go/clock.go#clock -->
```go
// Today reads the clock. It is a spring: read it here, once, and pass the date in.
func Today() time.Time {
	return time.Now() //nolint:forbidigo // the one place that reads the clock
}
```

The
[Go example](https://github.com/Aquilo-Solution-S/tesla-valve/tree/main/examples/go)
runs every enforcer above, and each is fed a file it must refuse.
