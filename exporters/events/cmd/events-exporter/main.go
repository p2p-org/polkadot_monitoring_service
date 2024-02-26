package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net"
	"net/http"
	"os"
	"substrate-events-exporter/internal/monitoring"
	"time"

	"github.com/kelseyhightower/envconfig"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"github.com/sirupsen/logrus"
	"golang.org/x/sync/errgroup"
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
		l.WithError(err).Warnf("unable to parse LOG_LEVEL %s", cfg.LogLevel)
		loglvl = logrus.InfoLevel
	}
	l.SetLevel(loglvl)

	temp, _ := json.Marshal(cfg)
	l.Infof("starting events exporter with following config: %s", temp)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	reader, err := NewHeadReader(l, cfg, ctx)
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
	g, ctx := errgroup.WithContext(ctx)
	go func() error {
		listener, err := net.Listen("tcp", cfg.MetricsListen)
		if err != nil {
			l.WithError(err).Fatalf("unable to start listening %s", cfg.MetricsListen)
			return err
		} else {
			l.Infof("started listener %s", cfg.MetricsListen)
		}
		server := &http.Server{
			Handler:           http.DefaultServeMux,
			ReadTimeout:       30 * time.Second,
			WriteTimeout:      30 * time.Second,
			ReadHeaderTimeout: 30 * time.Second,
			IdleTimeout:       30 * time.Second,
		}
		return server.Serve(listener)
	}() //nolint:errcheck
	g.Go(func() error {
		return reader.Read(ctx)
	})
	if err := g.Wait(); err != nil {
		l.WithError(err).Fatal("terminated")
	} else {
		l.Info("normal exit")
	}
}
