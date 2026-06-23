"""The Resource Gateway (spec §6).

The Gateway is ASKP's data plane: it authenticates each request's Access Token, runs the
pre-flight validation pipeline (§6.3), resolves the Provider Credential in-boundary, and proxies
the call to the upstream Provider as a transparent passthrough (§6.1).
"""
