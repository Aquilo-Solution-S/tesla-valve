# Driftfall

CI commands (run in this directory):

```sh
test -z "$(gofmt -l .)"
go vet ./...
go test ./...
```

Build offline and run the binary as a JSON-lines process.
