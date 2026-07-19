// Package apierrors defines ASKP's stable, machine-readable error vocabulary
// (protocol spec §8) and the JSON envelope returned to clients.
//
// It is deliberately framework-agnostic so that SDKs and third-party
// implementations may import it to encode and decode ASKP error responses. The
// set of codes is a closed vocabulary: values MUST NOT be repurposed with
// different meanings (spec §10 stability commitment).
package apierrors

import "net/http"

// Code is a stable, machine-readable error identifier.
type Code string

// Spec §8 error vocabulary.
const (
	InvalidToken        Code = "invalid_token"
	TokenRevoked        Code = "token_revoked"
	InsufficientScope   Code = "insufficient_scope"
	PolicyDenied        Code = "policy_denied"
	TenantIsolation     Code = "tenant_isolation"
	RateLimited         Code = "rate_limited"
	BudgetExceeded      Code = "budget_exceeded"
	ProviderError       Code = "provider_error"
	ProviderUnavailable Code = "provider_unavailable"
)

// Implementation-defined codes. These extend the spec's vocabulary without
// repurposing any spec code.
const (
	InvalidRequest       Code = "invalid_request"
	UnsupportedOperation Code = "unsupported_operation"
	NotConfigured        Code = "not_configured"
	Internal             Code = "internal_error"
)

// httpStatus maps each code to its canonical HTTP status.
var httpStatus = map[Code]int{
	InvalidToken:         http.StatusUnauthorized,
	TokenRevoked:         http.StatusUnauthorized,
	InsufficientScope:    http.StatusForbidden,
	PolicyDenied:         http.StatusForbidden,
	TenantIsolation:      http.StatusForbidden,
	RateLimited:          http.StatusTooManyRequests,
	BudgetExceeded:       http.StatusTooManyRequests,
	ProviderError:        http.StatusBadGateway,
	ProviderUnavailable:  http.StatusServiceUnavailable,
	InvalidRequest:       http.StatusBadRequest,
	UnsupportedOperation: http.StatusNotFound,
	NotConfigured:        http.StatusServiceUnavailable,
	Internal:             http.StatusInternalServerError,
}

// Error is an ASKP error carrying a stable Code and a human-readable message.
// It implements the error interface so it can flow through normal Go error
// handling and be mapped to an HTTP response at the edge.
type Error struct {
	Code        Code
	Description string
}

// New builds an Error with the given code and description.
func New(code Code, description string) *Error {
	return &Error{Code: code, Description: description}
}

// Error implements the error interface.
func (e *Error) Error() string {
	if e.Description == "" {
		return string(e.Code)
	}
	return string(e.Code) + ": " + e.Description
}

// HTTPStatus returns the canonical HTTP status for this error's code.
func (e *Error) HTTPStatus() int {
	if s, ok := httpStatus[e.Code]; ok {
		return s
	}
	return http.StatusInternalServerError
}

// Envelope is the JSON body shape returned for every ASKP error (spec §8).
type Envelope struct {
	Error       Code   `json:"error"`
	Description string `json:"error_description,omitempty"`
	RequestID   string `json:"request_id,omitempty"`
}

// AsEnvelope renders this error as a wire Envelope stamped with the request id.
func (e *Error) AsEnvelope(requestID string) Envelope {
	return Envelope{Error: e.Code, Description: e.Description, RequestID: requestID}
}
