FROM golangci/golangci-lint:v1.56-alpine as linter
WORKDIR /build/
COPY . .
RUN golangci-lint run --timeout=360s

FROM golang:1.22-alpine as builder

WORKDIR /build/
COPY --from=linter /build/go.mod /build/go.sum ./
RUN go mod download && go mod verify

COPY --from=linter /build/ .
RUN \
  go build -v -o events-exporter ./cmd/events-exporter/

FROM alpine:3.19
COPY --from=builder /build/events-exporter /app/
WORKDIR /app
ENTRYPOINT ["/app/events-exporter"]