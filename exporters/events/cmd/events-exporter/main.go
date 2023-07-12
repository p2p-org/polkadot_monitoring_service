package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"substrate-events-exporter/internal/monitoring"
	"syscall"

	"github.com/kelseyhightower/envconfig"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
)

func main() {
	l := logrus.New()
	l.SetOutput(os.Stdout)
	l.SetReportCaller(true)
	l.SetFormatter(&logrus.TextFormatter{})
	var err error
	var cfg Config
	err = envconfig.Process("", &cfg)
	if err != nil {
		l.Fatal(err)
	}
	loglvl, err := logrus.ParseLevel(cfg.LogLevel)
	if err != nil {
		l.WithError(err).Warn("unable to parse LOG_LEVEL %s", cfg.LogLevel)
		loglvl = logrus.InfoLevel
	}
	l.SetLevel(loglvl)

	temp, _ := json.Marshal(cfg)
	l.Infof("starting events exporter with following config: %s", temp)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	reader, err := NewEventsReader(l, cfg, ctx)
	if err != nil {
		l.WithError(err).Fatalln("unable to create events reader")
	}
	mon := monitoring.NewMetrics()
	mon.Register(reader)
	http.Handle("/metrics", promhttp.Handler())
	http.HandleFunc("/healthz", func(w http.ResponseWriter, r *http.Request) {
		if reader.EventsRate == 0 {
			w.WriteHeader(http.StatusNotFound)
			fmt.Println(w, "no new events for 3 min")
		} else {
			fmt.Fprintf(w, "Ok")
		}
	})
	go http.ListenAndServe(cfg.MetricsListen, nil)
	go reader.Read(ctx)
	ch := make(chan os.Signal, 1)
	signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
	l.Infof("Normal termination, signal %s", <-ch)
}
