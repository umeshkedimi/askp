package middleware

import (
	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"github.com/umeshkedimi/askp/pkg/apierrors"
)

// Recovery converts a handler panic into a stable internal_error response and
// logs the panic, so a stack trace never leaks to the client.
func Recovery(logger *zap.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		defer func() {
			if r := recover(); r != nil {
				requestID := RequestIDFromContext(c)
				logger.Error("panic recovered",
					zap.Any("panic", r),
					zap.String("request_id", requestID),
				)
				err := apierrors.New(apierrors.Internal, "internal server error")
				c.AbortWithStatusJSON(err.HTTPStatus(), err.AsEnvelope(requestID))
			}
		}()
		c.Next()
	}
}
