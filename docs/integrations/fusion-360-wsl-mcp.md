# Fusion 360 MCP server from WSL2

This guide covers a setup where the Safe Agent container runs from Docker
inside WSL2 and needs to connect to a Fusion 360 MCP service exposed through
the Windows host.

## Network layout

The relevant processes are separate:

```text
Safe Agent container
        |
        | Docker host mapping
        v
Windows host / Fusion 360 MCP service
```

`localhost` in the agent container does not refer to Windows or WSL. The
container therefore needs a host mapping for the Windows-side gateway address.

## Find the Windows gateway address

From the WSL environment, run:

```bash
ip route | awk '/default/ {print $3; exit}'
```

For example, this may return:

```text
172.25.240.1
```

The address can change after restarting WSL, restarting Windows, changing
network connections, or using a VPN. Re-run the command whenever the MCP
connection stops working.

## Configure the safe project

Create or update `.safe-agent.toml` in the root of the safe project:

```toml
[docker.hosts]
"windows-host" = "172.25.240.1"
```

Replace the example address with the value returned by `ip route`. The
`windows-host` name is an alias; configure the MCP client inside the agent to
connect to that name and the MCP server's port.

For example, if the MCP server listens on port `8000`, its endpoint would use
the equivalent of:

```text
http://windows-host:8000
```

Use the actual transport and port required by the MCP server.

## Connectivity requirements

The MCP service must:

- listen on an address reachable from the Docker network, not only an
  inaccessible loopback address;
- be listening on the configured port; and
- be allowed through Windows Firewall if the firewall blocks the connection.

If the client cannot connect, first verify the current gateway address and
then test the MCP endpoint from a temporary container using the same host
mapping. A stale gateway address is the most likely cause after a WSL or
network restart.

This setup intentionally uses a literal address in the project configuration.
Safe Agent does not contain Fusion-specific or WSL route-discovery logic; the
launcher simply passes the configured Docker host mapping through to Docker.
