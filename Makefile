BINARY := askp
PKG := ./...

.PHONY: help build run test vet lint fmt tidy docker

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-10s\033[0m %s\n", $$1, $$2}'

build: ## Compile the askp binary into ./bin
	go build -o bin/$(BINARY) ./cmd/askp

run: ## Run the ASKP server locally
	go run ./cmd/askp serve

test: ## Run tests with the race detector
	go test -race $(PKG)

vet: ## Run go vet
	go vet $(PKG)

lint: ## Run golangci-lint
	golangci-lint run

fmt: ## Format and tidy imports
	go fmt $(PKG)

tidy: ## Tidy go.mod / go.sum
	go mod tidy

docker: ## Build the container image
	docker build -f deploy/docker/Dockerfile -t askp:dev .
