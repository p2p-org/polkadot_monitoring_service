FROM golangci/golangci-lint:v1.53-alpine as linter
WORKDIR /build/
COPY . .
RUN golangci-lint run

FROM golang:1.20-alpine as builder

WORKDIR /build/
COPY --from=linter /build/go.mod /build/go.sum ./
RUN go mod download && go mod verify

COPY --from=linter /build/ .
RUN \
  go build -v -o events-exporter ./cmd/events-exporter/

FROM alpine:3.17
COPY --from=builder /build/events-exporter /app/
WORKDIR /app
ENTRYPOINT ["/app/events-exporter"]