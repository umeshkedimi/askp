// Package metrics owns ASKP's Prometheus registry and HTTP instrumentation.
package metrics

import (
	"net/http"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/collectors"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Registry holds ASKP's metric collectors and their Prometheus registry. Using a
// private registry (rather than the global default) keeps metrics isolated per
// process and makes the server testable.
type Registry struct {
	reg             *prometheus.Registry
	requestsTotal   *prometheus.CounterVec
	requestDuration *prometheus.HistogramVec
}

// New creates a Registry with ASKP's standard HTTP and runtime metrics.
func New() *Registry {
	reg := prometheus.NewRegistry()
	reg.MustRegister(
		collectors.NewGoCollector(),
		collectors.NewProcessCollector(collectors.ProcessCollectorOpts{}),
	)

	requestsTotal := prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Namespace: "askp",
			Subsystem: "http",
			Name:      "requests_total",
			Help:      "Total HTTP requests by method, route and status.",
		},
		[]string{"method", "route", "status"},
	)
	requestDuration := prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Namespace: "askp",
			Subsystem: "http",
			Name:      "request_duration_seconds",
			Help:      "HTTP request latency by method and route.",
			Buckets:   prometheus.DefBuckets,
		},
		[]string{"method", "route"},
	)
	reg.MustRegister(requestsTotal, requestDuration)

	return &Registry{
		reg:             reg,
		requestsTotal:   requestsTotal,
		requestDuration: requestDuration,
	}
}

// Handler returns the HTTP handler that exposes the registry (mounted at
// /metrics by the router).
func (r *Registry) Handler() http.Handler {
	return promhttp.HandlerFor(r.reg, promhttp.HandlerOpts{})
}

// Middleware records request counts and latency. It labels by the matched route
// template (not the raw path) to bound metric cardinality.
func (r *Registry) Middleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		c.Next()

		route := c.FullPath()
		if route == "" {
			route = "unmatched"
		}
		r.requestDuration.WithLabelValues(c.Request.Method, route).
			Observe(time.Since(start).Seconds())
		r.requestsTotal.WithLabelValues(
			c.Request.Method, route, strconv.Itoa(c.Writer.Status()),
		).Inc()
	}
}
