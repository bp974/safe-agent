# Safe Codex

A Docker-based environment for running OpenAI Codex against isolated copies of local Git repositories.

The goal is to allow Codex to modify project source code without giving the container access to the real development directory, `.env` files, SSH keys, or other files in the host user's home directory.

## Security Model

Real projects live under:

```text
~/git/
```

For example:

```text
~/git/summit-application/
├── .git/
├── .env
├── app.js
└── ...
```

Codex does **not** work directly against this directory.

Instead, an independent Git clone is kept under:

```text
~/git/safe-codex/work/
```

For example:

```text
~/git/safe-codex/work/summit-application/
```

The Codex Docker container receives only two host mounts:

```text
Safe project clone  -> /workspace
Codex home          -> /root/.codex
```

The real project directory is never mounted into the container.

Therefore files such as:

```text
~/git/summit-application/.env
~/.ssh/
other ~/git projects
other files in ~/
```

are not visible to Codex through the container filesystem.

## Directory Layout

```text
~/git/
├── safe-codex/
│   ├── bin/
│   │   ├── codex-start
│   │   ├── codex-pull
│   │   └── codex-push
│   │
│   ├── container/
│   │   ├── Dockerfile
│   │   └── home/               # ignored; contains Codex auth/config
│   │
│   ├── work/                   # ignored; contains AI-safe clones
│   │   ├── summit-application/
│   │   └── ...
│   │
│   ├── .gitignore
│   └── README.md
│
├── summit-application/         # real project
│   └── .env
│
└── ...
```

## Commands

### `codex-start`

Starts Codex inside the Docker container.

Run it from an AI-safe project:

```bash
cd ~/git/safe-codex/work/summit-application
codex-start
```

The script refuses to start Codex from directories outside:

```text
~/git/safe-codex/work/
```

Only the current safe project is mounted as `/workspace`.

Codex authentication and configuration are persisted through:

```text
~/git/safe-codex/container/home/
```

This directory is sensitive and must never be committed.

### `codex-pull`

Updates the AI-safe project from the corresponding real repository.

Run from the safe project:

```bash
cd ~/git/safe-codex/work/summit-application
codex-pull
```

Direction:

```text
REAL PROJECT
     |
     v
SAFE CODEX COPY
```

Synchronization is Git-based and uses committed history.

Uncommitted files, ignored files, and `.env` files are not copied.

The safe working tree must be clean before synchronization.

### `codex-push`

Imports committed Codex changes into the real project.

Run from the safe project:

```bash
cd ~/git/safe-codex/work/summit-application
codex-push
```

Direction:

```text
SAFE CODEX COPY
     |
     v
REAL PROJECT
```

Before importing, the script:

1. Requires both working trees to be clean.
2. Fetches the committed Codex changes.
3. Verifies that the import can be performed as a Git fast-forward.
4. Displays the commits and files being imported.
5. Requires interactive confirmation.
6. Fast-forwards the real repository.

If the repositories have diverged, the import is refused rather than automatically merging them.

## Normal Workflow

Start with work in the real repository committed:

```bash
cd ~/git/summit-application
git status
```

Move to the corresponding safe clone:

```bash
cd ~/git/safe-codex/work/summit-application
```

Bring in the latest committed real-project changes:

```bash
codex-pull
```

Start Codex:

```bash
codex-start
```

Have Codex make and commit its changes.

After exiting Codex, review the safe repository:

```bash
git status
git log --oneline
git diff HEAD~1
```

When satisfied:

```bash
codex-push
```

Review the import preview and confirm it.

Then return to the real project:

```bash
cd ~/git/summit-application
```

Test normally using the real development environment and `.env`.

Push through the normal Git workflow when ready.

## Adding a Project

Create a safe clone under `work/`.

For example:

```bash
cd ~/git/safe-codex/work
git clone ~/git/example-project example-project
```

The project directory name should match the real project directory name:

```text
~/git/example-project
~/git/safe-codex/work/example-project
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

Before using Codex, verify that secrets were not committed into the repository:

```bash
find . \
  \( -name ".env" \
  -o -name ".env.*" \
  -o -name "*.pem" \
  -o -name "*.key" \) \
  -print
```

Files such as `.env.example` may be intentionally present if they contain only non-secret example values.

## Building the Container

From the Safe Codex repository:

```bash
cd ~/git/safe-codex
docker build -t codex-dev ./container
```

The image contains the Codex CLI and development tools required for the isolated environment.

Git identity is configured inside the image so Codex can create commits without mounting the host's `~/.gitconfig`.

Rebuild the image after modifying the Dockerfile:

```bash
docker build -t codex-dev ./container
```

## Codex Configuration

Codex state is stored at:

```text
~/git/safe-codex/container/home/
```

Inside the container this is mounted at:

```text
/root/.codex
```

This allows authentication and Codex configuration to survive container recreation.

The directory may contain authentication credentials and must:

- remain excluded by `.gitignore`
- never be shared
- never be committed to Git

## Important Security Rules

Do not modify the Docker launcher to mount:

```text
~/git
~
~/.ssh
~/.gitconfig
/var/run/docker.sock
```

The security boundary depends on the Codex container having access only to the safe project copy and its own Codex configuration directory.

Never place real credentials in the safe project clone.

Keep secrets such as `.env` files exclusively in the real development repository and ensure they are excluded from Git.

## Design Principle

The intended trust boundary is:

```text
                    HOST

        Real project
        + credentials
        + .env
             ^
             |
        Git push/pull
             |
             v
       Safe Git clone
             |
             | bind mount
             v
    +-------------------+
    |  Codex container  |
    |                   |
    |    /workspace     |
    +-------------------+
```

Codex operates on a disposable, credential-free Git copy.

Git commits are the controlled bridge between that copy and the real development repository.

## Keeping Git History Clean

During development, multiple `codex-push` / `codex-pull` cycles are fine. Codex commits can be treated as temporary checkpoints until the work is ready to push upstream.

Typical workflow:

```text
codex-pull
codex-start
codex-push
test
codex-pull
codex-start
codex-push
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

This keeps the intermediate Codex commits locally useful during development while only publishing the final clean commit.

> **Note:** This squashes **all** local commits since `origin/main`, not only Codex commits. Only use it when those commits should all become one logical change.
