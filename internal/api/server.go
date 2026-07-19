// Package api assembles ASKP's HTTP surface: the Gin engine, the middleware
// chain, and route registration.
//
// The router is built from Settings plus already-constructed dependencies (a
// logger, a metrics registry, readiness checkers), never from package globals,
// so tests can build fully isolated servers and future increments can assemble
// differently-scoped Issuer/Gateway/Admin processes from the same factory.
package api

import (
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"github.com/umeshkedimi/askp/internal/config"
	"github.com/umeshkedimi/askp/internal/metrics"
	"github.com/umeshkedimi/askp/internal/middleware"
)

// Options carries the constructed dependencies an HTTP server needs.
type Options struct {
	Settings *config.Settings
	Logger   *zap.Logger
	Metrics  *metrics.Registry
	// Checkers are evaluated by the /ready probe. Empty in Increment 0; Postgres
	// and Redis are registered in Increment 1.
	Checkers []Checker
}

// NewRouter builds the fully-wired Gin engine.
func NewRouter(opts Options) *gin.Engine {
	if opts.Settings.IsProduction() {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.New()
	r.Use(
		middleware.RequestID(),
		middleware.Recovery(opts.Logger),
		middleware.Logger(opts.Logger),
	)
	if opts.Metrics != nil {
		r.Use(opts.Metrics.Middleware())
		r.GET("/metrics", gin.WrapH(opts.Metrics.Handler()))
	}

	r.GET("/health", healthHandler)
	r.GET("/ready", readinessHandler(opts.Checkers))

	return r
}
