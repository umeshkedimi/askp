// Package logging builds the process-wide zap logger from Settings.
package logging

import (
	"fmt"

	"go.uber.org/zap"
	"go.uber.org/zap/zapcore"

	"github.com/umeshkedimi/askp/internal/config"
)

// New constructs a zap.Logger honoring the configured level and format. It never
// logs credentials or full tokens; call sites are responsible for redaction.
func New(s *config.Settings) (*zap.Logger, error) {
	level, err := zapcore.ParseLevel(normalizeLevel(s.LogLevel))
	if err != nil {
		return nil, fmt.Errorf("logging: parse level %q: %w", s.LogLevel, err)
	}

	var cfg zap.Config
	if s.UseJSONLogs() {
		cfg = zap.NewProductionConfig()
	} else {
		cfg = zap.NewDevelopmentConfig()
		cfg.EncoderConfig.EncodeLevel = zapcore.CapitalColorLevelEncoder
	}
	cfg.Level = zap.NewAtomicLevelAt(level)
	cfg.EncoderConfig.TimeKey = "ts"
	cfg.EncoderConfig.EncodeTime = zapcore.ISO8601TimeEncoder

	logger, err := cfg.Build()
	if err != nil {
		return nil, fmt.Errorf("logging: build: %w", err)
	}
	return logger.With(zap.String("app", s.AppName)), nil
}

// normalizeLevel accepts the human-friendly "warning" alias used in config and
// maps it to zap's "warn".
func normalizeLevel(level string) string {
	if level == "warning" {
		return "warn"
	}
	return level
}
