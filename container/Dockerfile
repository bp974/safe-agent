FROM node:22-bookworm

RUN apt-get update && apt-get install -y \
    git \
    bash \
    netcat-openbsd \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install supported coding agents.
RUN npm install -g \
    @openai/codex \
    @anthropic-ai/claude-code \
    @opencode/cli

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

CMD ["bash"]
