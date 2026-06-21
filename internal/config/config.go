// Package config loads ASKP's runtime configuration from environment variables.
//
// This follows the "twelve-factor" approach: configuration lives in the environment, not in
// code, so the same compiled binary runs unchanged across dev / staging / prod. Every setting is
// overridable with an ASKP_-prefixed variable, e.g. ASKP_PORT=9000 or ASKP_LOG_LEVEL=debug.
//
// We deliberately use only the standard library (os, strconv) rather than a config framework:
// the surface is small, and reading it teaches what such frameworks do under the hood.
package config

import (
	"fmt"
	"os"
	"strconv"
)

// Environment is the deployment environment. It influences defaults like log formatting.
type Environment string

const (
	EnvDevelopment Environment = "development"
	EnvStaging     Environment = "staging"
	EnvProduction  Environment = "production"
)

// Config is the fully-resolved, validated configuration for one running process.
//
// In Go we model config as a plain struct and pass it explicitly to the components that need it
// (dependency injection by hand). There is no global singleton like Python's lru_cache'd
// get_settings(); instead we Load() once in main() and thread the *Config through.
type Config struct {
	// Service identity
	AppName     string
	Environment Environment

	// HTTP server
	Host string
	Port int

	// Observability
	LogLevel string
	LogJSON  bool

	// Datastores (used from Increment 1 onward; declared now so config is stable).
	DatabaseURL string
	RedisURL    string
}

// Load reads configuration from the environment, applies defaults, and validates it.
//
// It returns an error (rather than panicking) so the caller — main() — decides how to fail.
// This is idiomatic Go: libraries return errors; the program's entry point chooses the exit.
func Load() (*Config, error) {
	env := Environment(getenv("ASKP_ENVIRONMENT", string(EnvDevelopment)))

	port, err := strconv.Atoi(getenv("ASKP_PORT", "8000"))
	if err != nil {
		return nil, fmt.Errorf("ASKP_PORT must be an integer: %w", err)
	}

	c := &Config{
		AppName:     getenv("ASKP_APP_NAME", "askp"),
		Environment: env,
		Host:        getenv("ASKP_HOST", "127.0.0.1"),
		Port:        port,
		LogLevel:    getenv("ASKP_LOG_LEVEL", "info"),
		// pgx / database/sql DSN form (not SQLAlchemy's "postgresql+asyncpg://").
		DatabaseURL: getenv("ASKP_DATABASE_URL", "postgres://askp:askp@localhost:5432/askp?sslmode=disable"),
		RedisURL:    getenv("ASKP_REDIS_URL", "redis://localhost:6379/0"),
	}

	// LogJSON resolution: an explicit ASKP_LOG_JSON wins; otherwise emit JSON everywhere except
	// development (where human-readable text is friendlier).
	if v, ok := os.LookupEnv("ASKP_LOG_JSON"); ok {
		b, err := strconv.ParseBool(v)
		if err != nil {
			return nil, fmt.Errorf("ASKP_LOG_JSON must be a boolean: %w", err)
		}
		c.LogJSON = b
	} else {
		c.LogJSON = env != EnvDevelopment
	}

	return c, nil
}

// IsProduction reports whether the process runs in the production environment.
func (c *Config) IsProduction() bool { return c.Environment == EnvProduction }

// Addr returns the host:port string the HTTP server binds to.
func (c *Config) Addr() string { return fmt.Sprintf("%s:%d", c.Host, c.Port) }

// getenv returns the value of key, or def if the variable is unset or empty.
func getenv(key, def string) string {
	if v, ok := os.LookupEnv(key); ok && v != "" {
		return v
	}
	return def
}
