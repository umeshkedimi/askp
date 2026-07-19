// Package cli defines the askp command-line interface.
package cli

import (
	"os/signal"
	"syscall"

	"github.com/spf13/cobra"

	"github.com/umeshkedimi/askp/internal/app"
	"github.com/umeshkedimi/askp/internal/config"
)

// NewRootCommand builds the root `askp` command and its subcommands.
func NewRootCommand() *cobra.Command {
	root := &cobra.Command{
		Use:           "askp",
		Short:         "ASKP — secure, scoped access to AI providers",
		Long:          "ASKP (AI Secure Key Protocol) brokers scoped, short-lived access to AI providers without exposing raw provider credentials to clients.",
		SilenceUsage:  true,
		SilenceErrors: true,
	}
	root.AddCommand(newServeCommand())
	return root
}

// newServeCommand runs the ASKP HTTP server until interrupted.
func newServeCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "serve",
		Short: "Run the ASKP HTTP server",
		RunE: func(cmd *cobra.Command, _ []string) error {
			settings, err := config.Load()
			if err != nil {
				return err
			}
			ctx, stop := signal.NotifyContext(cmd.Context(), syscall.SIGINT, syscall.SIGTERM)
			defer stop()
			return app.Run(ctx, settings)
		},
	}
}
