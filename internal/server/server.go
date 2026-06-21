// Package server wires ASKP's HTTP layer: routing, the http.Server, and its graceful lifecycle.
//
// This is the Go equivalent of the Python "app factory": New() assembles a server from its
// dependencies (config, logger, and — later — the database and Redis), and Run() owns the
// start/stop lifecycle.
package server

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"time"

	"github.com/umeshkedimi/askp/internal/config"
)

// Server holds the HTTP server and the dependencies its handlers need.
type Server struct {
	cfg  *config.Config
	log  *slog.Logger
	http *http.Server
}

// New constructs a Server. It builds the route table and the underlying *http.Server but does
// not start listening — that is Run's job.
func New(cfg *config.Config, log *slog.Logger) *Server {
	s := &Server{cfg: cfg, log: log}

	mux := http.NewServeMux()
	s.routes(mux)

	s.http = &http.Server{
		Addr:    cfg.Addr(),
		Handler: mux,
		// Always bound how long we'll wait for request headers: a cheap defence against slow,
		// resource-holding clients (Slowloris-style).
		ReadHeaderTimeout: 10 * time.Second,
	}
	return s
}

// routes registers all HTTP routes. Go 1.22+ lets us put the method in the pattern
// ("GET /health"), so the router itself rejects wrong-method requests.
func (s *Server) routes(mux *http.ServeMux) {
	mux.HandleFunc("GET /health", s.handleHealth)
	mux.HandleFunc("GET /ready", s.handleReady)
}

// Run starts the HTTP server and blocks until ctx is cancelled (e.g. on SIGINT/SIGTERM) or the
// server fails, then shuts down gracefully, draining in-flight requests.
func (s *Server) Run(ctx context.Context) error {
	// ListenAndServe blocks, so run it in a goroutine and report failures over a channel.
	errCh := make(chan error, 1)
	go func() {
		s.log.Info("http server listening", "addr", s.http.Addr)
		if err := s.http.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
	}()

	select {
	case err := <-errCh:
		return err
	case <-ctx.Done():
		s.log.Info("shutting down http server")
		// Give in-flight requests up to 10s to finish before forcing the close.
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		return s.http.Shutdown(shutdownCtx)
	}
}
