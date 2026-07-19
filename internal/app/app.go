// Package app is ASKP's composition root: it wires configuration, logging,
// metrics, and the HTTP router together and runs the server with graceful
// shutdown. The CLI delegates to it so that wiring lives in one testable place.
package app

import (
	"context"
	"errors"
	"net/http"
	"time"

	"go.uber.org/zap"

	"github.com/umeshkedimi/askp/internal/api"
	"github.com/umeshkedimi/askp/internal/config"
	"github.com/umeshkedimi/askp/internal/logging"
	"github.com/umeshkedimi/askp/internal/metrics"
)

const (
	shutdownTimeout   = 15 * time.Second
	readHeaderTimeout = 10 * time.Second
)

// Run builds the server from settings and serves until ctx is cancelled, then
// drains in-flight requests within shutdownTimeout. It returns the first fatal
// error, or nil on a clean shutdown.
func Run(ctx context.Context, settings *config.Settings) error {
	logger, err := logging.New(settings)
	if err != nil {
		return err
	}
	defer func() { _ = logger.Sync() }()

	router := api.NewRouter(api.Options{
		Settings: settings,
		Logger:   logger,
		Metrics:  metrics.New(),
	})

	srv := &http.Server{
		Addr:              settings.Addr(),
		Handler:           router,
		ReadHeaderTimeout: readHeaderTimeout,
	}

	serveErr := make(chan error, 1)
	go func() {
		logger.Info("http server listening",
			zap.String("addr", settings.Addr()),
			zap.String("environment", string(settings.Environment)),
		)
		if err := srv.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			serveErr <- err
			return
		}
		serveErr <- nil
	}()

	select {
	case err := <-serveErr:
		return err
	case <-ctx.Done():
		logger.Info("shutdown signal received, draining connections")
		shutdownCtx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			logger.Error("graceful shutdown failed", zap.Error(err))
			return err
		}
		logger.Info("shutdown complete")
		return nil
	}
}
