package monitoring

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

type Observable interface {
	GetMonitoringEvents() []MonitoringEvent
	SetObserver(Observer)
}

type Observer interface {
	ProcessEvent(string, int, ...string)
	Register(Observable)
}
type MonitoringEvent struct {
	TypeName    string
	Name        string
	Description string
	Labels      []string
}

type PrometheusMetrics struct {
	events  map[string]MonitoringEvent
	metrics map[string]interface{}
}

const (
	TypeCounter = "Counter"
)

func (p *PrometheusMetrics) Register(t Observable) {
	t.SetObserver(p)
	for _, et := range t.GetMonitoringEvents() {
		switch et.TypeName {
		case TypeCounter:
			if len(et.Labels) != 0 {
				p.metrics[et.Name] = promauto.NewCounterVec(prometheus.CounterOpts{
					Name: et.Name,
					Help: et.Description,
				}, et.Labels)
			} else {
				p.metrics[et.Name] = promauto.NewCounter(prometheus.CounterOpts{
					Name: et.Name,
					Help: et.Description,
				})
			}
		}
		p.events[et.Name] = et
	}
}

func (p *PrometheusMetrics) ProcessEvent(name string, value int, lvs ...string) {
	if e, ok := p.events[name]; ok {
		switch e.TypeName {
		case TypeCounter:
			if c, ok := p.metrics[e.Name]; ok {
				if len(lvs) != 0 {
					c := c.(*prometheus.CounterVec)
					c.WithLabelValues(lvs...).Add(float64(value))
				} else {
					c := c.(prometheus.Counter)
					c.Add(float64(value))
				}
			}
		}
	}
}

func NewMetrics() PrometheusMetrics {
	return PrometheusMetrics{
		events:  make(map[string]MonitoringEvent),
		metrics: make(map[string]interface{}),
	}
}
