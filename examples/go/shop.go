// Package shop computes the delivery date at checkout, the step the manifesto
// walks through.
package shop

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"
)

// region: postcode
type Postcode struct{ code string }

func ParsePostcode(raw string) (Postcode, error) {
	code := strings.TrimSpace(raw)
	if len(code) != 5 || strings.Trim(code, "0123456789") != "" {
		return Postcode{}, errors.New("a postcode is five digits")
	}
	return Postcode{code: code}, nil
}

// endregion

// region: stock

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

// endregion

// region: spring
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

// endregion

func shippingDays(postcode Postcode) uint {
	if strings.HasPrefix(postcode.code, "1") {
		return 2
	}
	return 3
}
