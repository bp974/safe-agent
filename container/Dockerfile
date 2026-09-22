FROM node:22-bookworm

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install supported coding agents.
RUN npm install -g \
    @openai/codex \
    @anthropic-ai/claude-code \
    @opencode/cli

WORKDIR /workspace

CMD ["bash"]
