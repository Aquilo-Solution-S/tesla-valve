package shop

import (
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
