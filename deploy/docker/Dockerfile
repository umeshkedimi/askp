# syntax=docker/dockerfile:1

# ---- build stage ----
FROM golang:1.26-alpine AS build
WORKDIR /src

# Cache module downloads across source changes.
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/askp ./cmd/askp

# ---- runtime stage ----
# distroless/static: no shell, no package manager, runs as a non-root user.
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/askp /usr/local/bin/askp

# Bind to all interfaces inside the container (override per environment).
ENV ASKP_HOST=0.0.0.0
EXPOSE 8000

USER nonroot:nonroot
ENTRYPOINT ["askp"]
CMD ["serve"]
