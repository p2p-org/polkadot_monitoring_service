FROM golang:1.20-alpine as builder

WORKDIR /build/

COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .
RUN \
  go build -v -o events-exporter ./cmd/events-exporter/

FROM alpine:3.17
COPY --from=builder /build/events-exporter /app/
WORKDIR /app
ENTRYPOINT ["/app/events-exporter"]