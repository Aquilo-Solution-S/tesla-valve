# Driftfall

CI commands (run in this directory):

```sh
test -z "$(gofmt -l .)"
go vet ./...
go test ./...
```

The game binary is built from this directory with `go build -o game .` and runs as a
JSON-lines process.
