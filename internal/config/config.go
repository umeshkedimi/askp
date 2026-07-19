// Package config loads and validates ASKP runtime settings from environment
// variables (prefixed ASKP_) using Viper.
//
// Settings is constructed once at startup and injected into dependencies rather
// than read from package globals, so tests can build fully isolated processes.
// Validation is fail-closed: an invalid or unsafe configuration is a startup
// error, never a silently-degraded process.
package config

import (
	"fmt"
	"strings"

	"github.com/spf13/viper"
)

// Environment enumerates the deployment environments ASKP recognises.
type Environment string

// Recognised deployment environments.
const (
	EnvDevelopment Environment = "development"
	EnvStaging     Environment = "staging"
	EnvProduction  Environment = "production"
)

// Settings is the fully-resolved, validated configuration for one ASKP process.
type Settings struct {
	// Identity
	AppName     string      `mapstructure:"app_name"`
	Environment Environment `mapstructure:"environment"`

	// HTTP server
	Host string `mapstructure:"host"`
	Port int    `mapstructure:"port"`

	// Observability
	LogLevel  string `mapstructure:"log_level"`
	LogFormat string `mapstructure:"log_format"` // "json" | "console" | "auto"

	// Datastores (consumed from Increment 1 onward).
	DatabaseURL string `mapstructure:"database_url"`
	RedisURL    string `mapstructure:"redis_url"`
}

// configKeys is the canonical set of configuration keys. Each is registered with
// a default and bound to its ASKP_-prefixed environment variable.
var configKeys = []string{
	"app_name", "environment", "host", "port",
	"log_level", "log_format", "database_url", "redis_url",
}

// Load reads configuration from the environment (ASKP_ prefix), applies
// defaults, and validates the result.
func Load() (*Settings, error) {
	v := viper.New()
	v.SetEnvPrefix("ASKP")
	v.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))
	v.AutomaticEnv()

	v.SetDefault("app_name", "askp")
	v.SetDefault("environment", string(EnvDevelopment))
	v.SetDefault("host", "127.0.0.1")
	v.SetDefault("port", 8000)
	v.SetDefault("log_level", "info")
	v.SetDefault("log_format", "auto")
	v.SetDefault("database_url", "")
	v.SetDefault("redis_url", "")

	for _, key := range configKeys {
		// BindEnv makes AutomaticEnv values visible to Unmarshal even when no
		// config file is present.
		if err := v.BindEnv(key); err != nil {
			return nil, fmt.Errorf("config: bind %q: %w", key, err)
		}
	}

	var s Settings
	if err := v.Unmarshal(&s); err != nil {
		return nil, fmt.Errorf("config: unmarshal: %w", err)
	}
	if err := s.Validate(); err != nil {
		return nil, err
	}
	return &s, nil
}

// Validate enforces the invariants a running process depends on.
func (s *Settings) Validate() error {
	switch s.Environment {
	case EnvDevelopment, EnvStaging, EnvProduction:
	default:
		return fmt.Errorf("config: invalid environment %q (want development|staging|production)", s.Environment)
	}
	if s.Port < 1 || s.Port > 65535 {
		return fmt.Errorf("config: port %d out of range 1-65535", s.Port)
	}
	switch s.LogFormat {
	case "json", "console", "auto":
	default:
		return fmt.Errorf("config: invalid log_format %q (want json|console|auto)", s.LogFormat)
	}
	return nil
}

// IsProduction reports whether the process runs in the production environment.
func (s *Settings) IsProduction() bool { return s.Environment == EnvProduction }

// UseJSONLogs resolves the tri-state LogFormat: "auto" selects JSON everywhere
// except local development, where human-readable console output is friendlier.
func (s *Settings) UseJSONLogs() bool {
	switch s.LogFormat {
	case "json":
		return true
	case "console":
		return false
	default:
		return s.Environment != EnvDevelopment
	}
}

// Addr is the host:port the HTTP server binds to.
func (s *Settings) Addr() string {
	return fmt.Sprintf("%s:%d", s.Host, s.Port)
}
