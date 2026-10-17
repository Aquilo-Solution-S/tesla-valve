Run CI from this directory:

```sh
test -z "$(gofmt -l .)"
go vet ./...
go test ./...
```

Build: `go build -o game .` from the project root.
