package api

import (
	"context"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

// checkTimeout bounds how long the readiness probe waits on dependencies.
const checkTimeout = 3 * time.Second

// Checker reports the health of one dependency for the readiness probe.
// Postgres and Redis checkers are registered from Increment 1 onward.
type Checker interface {
	// Name identifies the dependency in the readiness response.
	Name() string
	// Check returns nil when the dependency is reachable.
	Check(ctx context.Context) error
}

// healthHandler is the liveness probe. It takes no dependencies, so a transient
// datastore outage never fails liveness (which would get the pod killed rather
// than merely pulled from the load balancer).
func healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{"status": "ok"})
}

// readinessHandler runs every registered Checker and returns 200 only when all
// dependencies are reachable, else 503 with a per-dependency breakdown.
func readinessHandler(checkers []Checker) gin.HandlerFunc {
	return func(c *gin.Context) {
		ctx, cancel := context.WithTimeout(c.Request.Context(), checkTimeout)
		defer cancel()

		checks := make(map[string]string, len(checkers))
		ready := true
		for _, ch := range checkers {
			if err := ch.Check(ctx); err != nil {
				ready = false
				checks[ch.Name()] = "error: " + err.Error()
				continue
			}
			checks[ch.Name()] = "ok"
		}

		status, state := http.StatusOK, "ready"
		if !ready {
			status, state = http.StatusServiceUnavailable, "not_ready"
		}
		c.JSON(status, gin.H{"status": state, "checks": checks})
	}
}
