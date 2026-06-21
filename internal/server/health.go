package server

import (
	"encoding/json"
	"net/http"
)

// handleHealth is the liveness probe. It has no dependencies and answers 200 as long as the
// process is running and able to serve HTTP. Orchestrators (Kubernetes, etc.) use liveness to
// decide whether to restart the container.
func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{
		"status":  "ok",
		"service": s.cfg.AppName,
	})
}

// handleReady is the readiness probe. From Increment 1 it will verify PostgreSQL and Redis
// connectivity and return 503 with a per-dependency breakdown when degraded. For now — before
// those datastores exist — it simply reports ready. Orchestrators use readiness to decide
// whether to route traffic to this instance.
func (s *Server) handleReady(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, http.StatusOK, map[string]any{"status": "ready"})
}

// writeJSON is a small helper to serialise a body as JSON with the right Content-Type. Order
// matters: set headers, then WriteHeader(status), then write the body.
func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
