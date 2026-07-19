# ASKP SDKs

This directory will host official client SDKs for ASKP once the HTTP surface
stabilises. Planned languages (see [`docs/README.md`](../docs/README.md) roadmap):

- Go
- Python
- TypeScript
- Java

SDKs are thin: they attach an ASKP access token to provider-native requests and
point the provider SDK's base URL at an ASKP Gateway. Adoption is meant to be a
base-URL-and-key change, nothing more.

> Nothing is published here yet. This is a placeholder tracking planned work.
