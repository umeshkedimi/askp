package server

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/umeshkedimi/askp/internal/config"
	"github.com/umeshkedimi/askp/internal/logging"
)

// newTestServer builds a Server suitable for handler tests. We don't open real sockets; we feed
// requests straight into the mux via httptest.
func newTestServer(t *testing.T) *Server {
	t.Helper()
	cfg := &config.Config{AppName: "askp-test"}
	return New(cfg, logging.New("error", false))
}

func TestHealth(t *testing.T) {
	srv := newTestServer(t)

	req := httptest.NewRequest(http.MethodGet, "/health", nil)
	rec := httptest.NewRecorder()
	srv.http.Handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}

	var body map[string]any
	if err := json.NewDecoder(rec.Body).Decode(&body); err != nil {
		t.Fatalf("decode body: %v", err)
	}
	if body["status"] != "ok" {
		t.Errorf("status field = %v, want %q", body["status"], "ok")
	}
	if body["service"] != "askp-test" {
		t.Errorf("service field = %v, want %q", body["service"], "askp-test")
	}
}

func TestReady(t *testing.T) {
	srv := newTestServer(t)

	req := httptest.NewRequest(http.MethodGet, "/ready", nil)
	rec := httptest.NewRecorder()
	srv.http.Handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusOK {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusOK)
	}
}

// TestHealthRejectsPost shows the Go 1.22+ method-aware router at work: POST to a GET-only route
// is a 405, with no handler code of ours involved.
func TestHealthRejectsPost(t *testing.T) {
	srv := newTestServer(t)

	req := httptest.NewRequest(http.MethodPost, "/health", nil)
	rec := httptest.NewRecorder()
	srv.http.Handler.ServeHTTP(rec, req)

	if rec.Code != http.StatusMethodNotAllowed {
		t.Fatalf("status = %d, want %d", rec.Code, http.StatusMethodNotAllowed)
	}
}
