// Command askp is the entrypoint for the ASKP reference implementation.
package main

import (
	"context"
	"fmt"
	"os"

	"github.com/umeshkedimi/askp/internal/cli"
)

func main() {
	if err := cli.NewRootCommand().ExecuteContext(context.Background()); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}
