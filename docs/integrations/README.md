# Integrations

These guides document application and host-service integrations that require
project-specific Docker configuration. They supplement the generic
`.safe-agent.toml` configuration documented in the main README without adding
application-specific behavior to `agent-start`.

## Available guides

- [Fusion 360 MCP server from WSL2](fusion-360-wsl-mcp.md)

## General pattern: reach a host service

If an agent container needs to reach a service outside the container, add a
name-to-address mapping to the safe project's `.safe-agent.toml`:

```toml
[docker.hosts]
"service-host" = "192.0.2.10"
```

Use the configured name, such as `service-host`, in the client configuration
inside the container. The address must be reachable from the Docker network;
`localhost` inside the container refers to the container itself.

Host addresses can be environment-specific and may change after a host,
virtual machine, WSL, VPN, or network restart. Keep machine-specific values
local to the safe project configuration when they are not appropriate for
other users.
