// Command askp is the ASKP reference-implementation binary.
//
// Usage:
//
//	askp serve   # start the HTTP server
//
// This file is intentionally thin: it parses the subcommand, loads config, builds the logger,
// and hands off to a component in internal/. Keeping main() small keeps the real logic testable
// (main() itself is hard to unit-test).
package main

import (
	"context"
	"fmt"
	"log/slog"
	"os"
	"os/signal"
	"syscall"

	"github.com/umeshkedimi/askp/internal/config"
	"github.com/umeshkedimi/askp/internal/logging"
	"github.com/umeshkedimi/askp/internal/server"
)

func main() {
	// The classic Go pattern: main() does nothing but call run() and translate an error into a
	// non-zero exit code. All real work — and all error returns — live in run().
	if err := run(os.Args); err != nil {
		fmt.Fprintln(os.Stderr, "askp:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) < 2 {
		return fmt.Errorf("usage: askp <command>\n\ncommands:\n  serve   start the HTTP server")
	}

	cfg, err := config.Load()
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}
	log := logging.New(cfg.LogLevel, cfg.LogJSON)

	switch args[1] {
	case "serve":
		return serve(cfg, log)
	default:
		return fmt.Errorf("unknown command %q (try: serve)", args[1])
	}
}

func serve(cfg *config.Config, log *slog.Logger) error {
	// signal.NotifyContext gives us a context that is cancelled on SIGINT (Ctrl-C) or SIGTERM
	// (what `docker stop` / Kubernetes send). The server watches this context to shut down
	// gracefully instead of being killed mid-request.
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()

	srv := server.New(cfg, log)
	return srv.Run(ctx)
}
