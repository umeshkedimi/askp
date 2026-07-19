package api

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"

	"go.uber.org/zap"

	"github.com/umeshkedimi/askp/internal/config"
	"github.com/umeshkedimi/askp/internal/metrics"
)

type stubChecker struct {
	name string
	err  error
}

func (s stubChecker) Name() string                { return s.name }
func (s stubChecker) Check(context.Context) error { return s.err }

func newTestOptions(checkers ...Checker) Options {
	return Options{
		Settings: &config.Settings{Environment: config.EnvDevelopment, LogFormat: "console", Port: 8000},
		Logger:   zap.NewNop(),
		Metrics:  metrics.New(),
		Checkers: checkers,
	}
}

func TestHealthEndpoint(t *testing.T) {
	r := NewRouter(newTestOptions())
	w := httptest.NewRecorder()
	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	r.ServeHTTP(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", w.Code)
	}
}

func TestReadyEndpointAllHealthy(t *testing.T) {
	r := NewRouter(newTestOptions(stubChecker{name: "postgres"}, stubChecker{name: "redis"}))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/ready", nil))

	if w.Code != http.StatusOK {
		t.Fatalf("status = %d, want 200", w.Code)
	}
	var body struct {
		Status string            `json:"status"`
		Checks map[string]string `json:"checks"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &body); err != nil {
		t.Fatalf("decode: %v", err)
	}
	if body.Status != "ready" {
		t.Errorf("status = %q, want ready", body.Status)
	}
}

func TestReadyEndpointDependencyDown(t *testing.T) {
	r := NewRouter(newTestOptions(stubChecker{name: "redis", err: errors.New("connection refused")}))
	w := httptest.NewRecorder()
	r.ServeHTTP(w, httptest.NewRequest(http.MethodGet, "/ready", nil))

	if w.Code != http.StatusServiceUnavailable {
		t.Fatalf("status = %d, want 503", w.Code)
	}
}
