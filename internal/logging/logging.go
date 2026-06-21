// Package logging configures ASKP's structured logger.
//
// We use log/slog, the standard library's structured logger (Go 1.21+), so we take on no
// third-party logging dependency. In development we emit human-friendly text; everywhere else we
// emit JSON so log aggregators (Loki, CloudWatch, Datadog, ...) can parse the fields.
package logging

import (
	"log/slog"
	"os"
	"strings"
)

// New builds a *slog.Logger at the given level. When jsonOutput is true it emits JSON lines,
// otherwise human-readable text.
func New(level string, jsonOutput bool) *slog.Logger {
	opts := &slog.HandlerOptions{Level: parseLevel(level)}

	var handler slog.Handler
	if jsonOutput {
		handler = slog.NewJSONHandler(os.Stdout, opts)
	} else {
		handler = slog.NewTextHandler(os.Stdout, opts)
	}
	return slog.New(handler)
}

// parseLevel maps our config strings to slog levels, defaulting to Info on anything unknown.
func parseLevel(level string) slog.Level {
	switch strings.ToLower(level) {
	case "debug":
		return slog.LevelDebug
	case "warning", "warn":
		return slog.LevelWarn
	case "error":
		return slog.LevelError
	default:
		return slog.LevelInfo
	}
}
