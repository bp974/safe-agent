# Safe Agent

A Docker-based environment for running AI coding agents against isolated copies of local Git repositories.

Supported agents:

- OpenAI Codex
- Claude Code
- OpenCode

The goal is to allow coding agents to modify project source code without giving the container access to the real development directory, `.env` files, SSH keys, or other files in the host user's home directory.

## Security Model

Real projects live under a user-configured project root.

For example:

```text
~/git/example-project/
├── .git/
├── .env
├── app.js
└── ...
```

Agents do **not** work directly against this directory.

Instead, independent Git clones are kept inside the Safe Agent installation:

```text
safe-agent/work/
```

For example:

```text
safe-agent/work/example-project/
```

The real project directory is never mounted into the container.

Therefore files such as:

```text
~/git/example-project/.env
~/.ssh/
other projects
other files in ~/
```

are not visible to the agent through the container filesystem.

Git commits provide the controlled bridge between the safe copy and the real repository.

## Directory Layout

Safe Agent can be cloned anywhere.

For example:

```text
~/git/
├── safe-agent/
│   ├── bin/
│   │   ├── agent-start
│   │   ├── agent-pull
│   │   └── agent-push
│   │
│   ├── container/
│   │   ├── Dockerfile
│   │   └── home/
│   │       ├── codex/
│   │       ├── claude/
│   │       └── opencode/
│   │           ├── config/
│   │           └── data/
│   │
│   ├── work/
│   │   ├── example-project/
│   │   └── ...
│   │
│   ├── .env
│   ├── .env.example
│   ├── .gitignore
│   └── README.md
│
├── example-project/
│   └── .env
│
└── ...
```

The Safe Agent scripts automatically determine where Safe Agent itself is installed.

The location of real projects is configured separately using `REAL_PROJECT_ROOT`.

`container/home/`, `work/`, and `.env` must be excluded from Git.

## Initial Setup

Clone Safe Agent wherever you want to keep it and enter the repository:

```bash
cd /path/to/safe-agent
```

Copy the example configuration:

```bash
cp .env.example .env
```

Configure your local settings:

```bash
GIT_USER_NAME="Your Name"
GIT_USER_EMAIL="you@example.com"
REAL_PROJECT_ROOT="$HOME/git"
DEFAULT_AGENT="codex"
```

`REAL_PROJECT_ROOT` is the directory containing your real development repositories.

For example:

```text
REAL_PROJECT_ROOT="$HOME/git"

$HOME/git/example-project
$HOME/git/another-project
```

Safe Agent does not need to be located inside `REAL_PROJECT_ROOT`.

For example, this is also valid:

```text
~/tools/safe-agent/
~/development/example-project/
```

with:

```bash
REAL_PROJECT_ROOT="$HOME/development"
```

Valid default agents are:

```text
codex
claude
opencode
```

The `.env` file contains local configuration and must never be committed.

## Add Safe Agent to PATH

Add the Safe Agent `bin` directory to your PATH.

For example:

```bash
export PATH="/path/to/safe-agent/bin:$PATH"
```

Add the appropriate line to `~/.zshrc`, `~/.bashrc`, or your shell's equivalent to make it permanent.

## Building the Container

From the Safe Agent repository:

```bash
docker build -t safe-agent ./container
```

The image contains:

- OpenAI Codex
- Claude Code
- OpenCode
- Git
- Common development/build tools

Git identity is supplied at runtime from `.env` rather than being stored in the Docker image.

Rebuild the image after modifying the Dockerfile:

```bash
docker build -t safe-agent ./container
```

## Commands

### `agent-start`

Starts an AI coding agent inside the isolated Docker container.

Run it from a project inside the Safe Agent `work/` directory:

```bash
cd /path/to/safe-agent/work/example-project
agent-start
```

With no argument, the agent configured by `DEFAULT_AGENT` in `.env` is used.

An agent can also be selected explicitly:

```bash
agent-start codex
agent-start claude
agent-start opencode
```

The explicit argument overrides `DEFAULT_AGENT`.

The script refuses to start from directories outside the Safe Agent `work/` directory.

Only the current safe project and the selected agent's required persistent state directories are mounted into the container.

### `agent-pull`

Updates the safe project from the corresponding real repository.

Run from the safe project:

```bash
cd /path/to/safe-agent/work/example-project
agent-pull
```

Direction:

```text
REAL PROJECT
     |
     v
SAFE AGENT COPY
```

The corresponding real project is determined from `REAL_PROJECT_ROOT` and the safe project's directory name.

For example:

```text
REAL_PROJECT_ROOT/example-project

        ↕

safe-agent/work/example-project
```

Synchronization is Git-based and uses committed history.

Uncommitted files, ignored files, and `.env` files are not copied.

Both working trees must be clean before pulling.

If the safe and real histories differ, such as after squashing commits in the real repository, `agent-pull` can reset the safe copy after explicit confirmation.

The real repository is never modified by this reset.

### `agent-push`

Imports committed agent changes into the corresponding real project.

Run from the safe project:

```bash
cd /path/to/safe-agent/work/example-project
agent-push
```

Direction:

```text
SAFE AGENT COPY
     |
     v
REAL PROJECT
```

Before pushing, the script:

1. Requires both working trees to be clean.
2. Fetches the committed safe-agent changes.
3. Verifies that the update can be performed as a Git fast-forward.
4. Displays the commits and files being transferred.
5. Requires interactive confirmation.
6. Fast-forwards the real repository.

If the repositories have diverged, the push is refused rather than automatically merging them.

## Normal Workflow

Start with work in the real repository committed:

```bash
cd "$REAL_PROJECT_ROOT/example-project"
git status
```

Move to the corresponding safe clone:

```bash
cd /path/to/safe-agent/work/example-project
```

Bring in the latest committed real-project changes:

```bash
agent-pull
```

Start your preferred agent:

```bash
agent-start
```

Or select one explicitly:

```bash
agent-start codex
agent-start claude
agent-start opencode
```

Have the agent make and commit its changes.

After exiting the agent, review the safe repository:

```bash
git status
git log --oneline
git diff HEAD~1
```

When satisfied:

```bash
agent-push
```

Review the preview and confirm it.

Then return to the real project and test normally using the real development environment and credentials.

Push through the normal Git workflow when ready.

## Adding a Project

Create a safe clone inside Safe Agent's `work/` directory.

For example:

```bash
cd /path/to/safe-agent/work
git clone "$REAL_PROJECT_ROOT/example-project" example-project
```

The safe project directory name must match the corresponding real project directory name:

```text
$REAL_PROJECT_ROOT/example-project

/path/to/safe-agent/work/example-project
```

Remove the automatically created local `origin`:

```bash
cd example-project
git remote remove origin
```

Verify:

```bash
git remote -v
```

No remote should be listed unless one is intentionally configured.

Before using an agent, verify that secrets were not committed into the repository:

```bash
find . \
  \( -name ".env" \
  -o -name ".env.*" \
  -o -name "*.pem" \
  -o -name "*.key" \) \
  -print
```

Files such as `.env.example` may be intentionally present if they contain only non-secret example values.

## Agent Configuration

Persistent agent state is stored under:

```text
safe-agent/container/home/
```

Each agent has isolated persistent storage:

```text
container/home/
├── codex/
├── claude/
└── opencode/
    ├── config/
    └── data/
```

Codex state is persisted from:

```text
/root/.codex
```

`CODEX_HOME` is explicitly set to this location.

OpenCode uses separate persistent configuration and data directories:

```text
/root/.config/opencode
/root/.local/share/opencode
```

These contain configuration, authentication, provider information, application data, and other persistent state.

Agent state directories may contain authentication credentials and must:

- remain excluded by `.gitignore`
- never be shared
- never be committed to Git

## Important Security Rules

Do not modify the Docker launcher to mount broad host locations such as:

```text
~
~/.ssh
~/.gitconfig
REAL_PROJECT_ROOT
/var/run/docker.sock
```

The security boundary depends on the container having access only to:

```text
the current safe project
+
the selected agent's required persistent state
```

The real development repository is deliberately **not** mounted into the container.

Never place real credentials in the safe project clone.

Keep secrets such as application `.env` files exclusively in the real development repository and ensure they are excluded from Git.

## Design Principle

The intended trust boundary is:

```text
                         HOST

                 Real project
                 + credentials
                 + .env
                      ^
                      |
                agent-push/pull
                      |
                      v
                 Safe Git clone
                      |
                      | bind mount
                      v
             +-------------------+
             |  Agent container  |
             |                   |
             |    /workspace     |
             +-------------------+
```

The coding agent operates on a credential-free Git copy.

Git commits are the controlled bridge between that copy and the real development repository.

## Keeping Git History Clean

During development, multiple `agent-push` / `agent-pull` cycles are fine. Agent commits can be treated as temporary checkpoints until the work is ready to push upstream.

Typical workflow:

```text
agent-pull
agent-start
agent-push
test

agent-pull
agent-start
agent-push
test
```

Before pushing the real repository upstream, squash all local commits since `origin/main` into one clean commit:

```bash
git fetch origin
git reset --soft origin/main
git status
git diff --cached --stat
git commit -m "Describe completed work"
git push
```

This keeps intermediate agent commits useful during development while only publishing the final clean commit.

After squashing, the safe repository will have different Git history. The next `agent-pull` will detect this and offer to reset the safe copy to match the real repository.

> **Note:** This squashes **all** local commits since `origin/main`, not only agent-generated commits. Only use it when those commits should all become one logical change.
