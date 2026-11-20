package shop

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

func date(year int, month time.Month, day int) time.Time {
	return time.Date(year, month, day, 0, 0, 0, 0, time.UTC)
}

func berlin(t *testing.T) Postcode {
	t.Helper()
	postcode, err := ParsePostcode("10115")
	if err != nil {
		t.Fatal(err)
	}
	return postcode
}

func TestOrderedOnTuesdayArrivesOnThursday(t *testing.T) {
	arrives := DeliveryDate(berlin(t), InStock{}, date(2026, time.October, 6))
	if want := date(2026, time.October, 8); !arrives.Equal(want) {
		t.Fatalf("arrives %s, want %s", arrives, want)
	}
}

func TestABackorderShipsOnceRestocked(t *testing.T) {
	arrives := DeliveryDate(berlin(t), Backorder{RestockDays: 5}, date(2026, time.October, 6))
	if want := date(2026, time.October, 13); !arrives.Equal(want) {
		t.Fatalf("arrives %s, want %s", arrives, want)
	}
}

// @holds backorder_not_sooner
func TestABackorderNeverArrivesSooner(t *testing.T) {
	today := date(2026, time.October, 6)
	inStock := DeliveryDate(berlin(t), InStock{}, today)
	for _, restockDays := range []uint16{0, 1, 30} {
		arrives := DeliveryDate(berlin(t), Backorder{RestockDays: restockDays}, today)
		if arrives.Before(inStock) {
			t.Errorf("restocked in %d days, it arrives %s, before %s", restockDays, arrives, inStock)
		}
	}
}

// @holds not_one_promise
func TestABackorderIsNotPromisedTheDateOfAnItemInStock(t *testing.T) {
	today := date(2026, time.October, 6)
	inStock := DeliveryDate(berlin(t), InStock{}, today)
	if DeliveryDate(berlin(t), Backorder{RestockDays: 1}, today).Equal(inStock) {
		t.Fatalf("a backorder is promised %s, the date of an item in stock", inStock)
	}
}

func TestTheCodeDecidesTheDaysTheSpecDecides(t *testing.T) {
	// @holds Vectors: `lake exe vectors`, in examples/lean, writes this file.
	raw, err := os.ReadFile("testdata/delivery_days.json")
	if err != nil {
		t.Fatal(err)
	}
	var vectors []struct {
		Shipping uint            `json:"shipping"`
		Stock    json.RawMessage `json:"stock"`
		Days     int             `json:"days"`
	}
	if err := json.Unmarshal(raw, &vectors); err != nil {
		t.Fatal(err)
	}
	today := date(2026, time.October, 6)
	for _, code := range []string{"10115", "20095"} {
		postcode, err := ParsePostcode(code)
		if err != nil {
			t.Fatal(err)
		}
		replayed := 0
		for _, vector := range vectors {
			if vector.Shipping != shippingDays(postcode) {
				continue
			}
			stock, err := StockOf(vector.Stock)
			if err != nil {
				t.Fatal(err)
			}
			arrives, want := DeliveryDate(postcode, stock, today), today.AddDate(0, 0, vector.Days)
			if !arrives.Equal(want) {
				t.Errorf("%s with %s arrives %s, want %s", code, vector.Stock, arrives, want)
			}
			replayed++
		}
		if replayed == 0 {
			t.Errorf("no vector ships in the days of %s", code)
		}
	}
}

func TestTheWarehouseSpringRefusesWhatItDoesNotKnow(t *testing.T) {
	for _, raw := range []string{
		`{"status":"discontinued"}`,
		`{"status":"backorder"}`,
		`{"status":"backorder","restock_days":-3}`,
		`{"status":"backorder","restock_days":70000}`,
	} {
		if _, err := StockOf([]byte(raw)); err == nil {
			t.Errorf("accepted %s", raw)
		}
	}
}

func TestTheCheckoutSpringRefusesWhatIsNotAPostcode(t *testing.T) {
	for _, raw := range []string{"1011", "101155", "1011a", "１０１１５"} {
		if _, err := ParsePostcode(raw); err == nil {
			t.Errorf("accepted %s", raw)
		}
	}
}
