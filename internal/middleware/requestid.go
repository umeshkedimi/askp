// Package middleware provides Gin middleware shared across ASKP HTTP surfaces:
// correlation ids, structured request logging, and panic recovery.
package middleware

import (
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

// HeaderRequestID is the header carrying the correlation id inbound and outbound.
const HeaderRequestID = "X-Request-ID"

const contextRequestID = "request_id"

// RequestID ensures every request has a correlation id: it honors an inbound
// X-Request-ID when present, otherwise generates one, stores it on the Gin
// context, and echoes it in the response so clients and traces can correlate.
func RequestID() gin.HandlerFunc {
	return func(c *gin.Context) {
		id := c.GetHeader(HeaderRequestID)
		if id == "" {
			id = uuid.NewString()
		}
		c.Set(contextRequestID, id)
		c.Header(HeaderRequestID, id)
		c.Next()
	}
}

// RequestIDFromContext returns the correlation id stored by RequestID, or "".
func RequestIDFromContext(c *gin.Context) string {
	if v, ok := c.Get(contextRequestID); ok {
		if id, ok := v.(string); ok {
			return id
		}
	}
	return ""
}
