#!/usr/bin/env python3
"""Read the data-only per-project Safe Agent configuration."""

import os
import sys
import tomllib
from typing import NoReturn


def fail(message: str) -> NoReturn:
    print(f"ERROR: invalid Safe Agent configuration: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    if len(sys.argv) != 2:
        fail("expected exactly one configuration file")

    path = sys.argv[1]

    try:
        with open(path, "rb") as config_file:
            config = tomllib.load(config_file)
    except OSError as error:
        fail(str(error))
    except tomllib.TOMLDecodeError as error:
        fail(str(error))

    unexpected_top_level = set(config) - {"mounts", "docker"}
    if unexpected_top_level:
        fail(
            "unknown top-level field(s): "
            + ", ".join(sorted(unexpected_top_level))
        )

    # Mounts
    mounts = config.get("mounts", [])
    if not isinstance(mounts, list):
        fail("'mounts' must be an array of tables")

    for index, mount in enumerate(mounts, start=1):
        if not isinstance(mount, dict):
            fail(f"mount {index} must be a table")

        unexpected = set(mount) - {"host", "container", "mode"}
        if unexpected:
            fail(
                f"mount {index} has unknown field(s): "
                f"{', '.join(sorted(unexpected))}"
            )

        missing = {"host", "container", "mode"} - set(mount)
        if missing:
            fail(f"mount {index} is missing: {', '.join(sorted(missing))}")

        host = mount["host"]
        container = mount["container"]
        mode = mount["mode"]

        if not all(isinstance(value, str) for value in (host, container, mode)):
            fail(f"mount {index} fields must all be strings")

        if not host or not container:
            fail(f"mount {index} paths must not be empty")

        if not os.path.isabs(host) or not os.path.isabs(container):
            fail(f"mount {index} paths must be absolute")

        if mode not in {"ro", "rw"}:
            fail(f"mount {index} mode must be 'ro' or 'rw'")

        if any(
            character in host or character in container
            for character in ("\x00", "\n", "\r", ":")
        ):
            fail(f"mount {index} paths contain an unsupported character")

        print(f"mount\t{host}:{container}:{mode}")

    # Docker settings
    docker = config.get("docker", {})
    if not isinstance(docker, dict):
        fail("'docker' must be a table")

    unexpected_docker = set(docker) - {"hosts"}
    if unexpected_docker:
        fail(
            "'docker' has unknown field(s): "
            + ", ".join(sorted(unexpected_docker))
        )

    hosts = docker.get("hosts", {})
    if not isinstance(hosts, dict):
        fail("'docker.hosts' must be a table")

    for name, value in hosts.items():
        if not isinstance(name, str) or not isinstance(value, str):
            fail("'docker.hosts' names and values must be strings")

        if not name or not value:
            fail("'docker.hosts' names and values must not be empty")

        if any(character in name or character in value
               for character in ("\x00", "\n", "\r", "\t")):
            fail("'docker.hosts' contains an unsupported character")

        print(f"host\t{name}={value}")

    return 0


if __name__ == "__main__":
    main()
