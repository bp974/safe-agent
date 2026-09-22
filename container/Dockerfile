FROM node:22-bookworm

RUN apt-get update && apt-get install -y \
    git \
    curl \
    ca-certificates \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN npm install -g @openai/codex

RUN git config --system user.name "Brett Pelkey" && \
    git config --system user.email "btp974@gmail.com"

WORKDIR /workspace

CMD ["codex"]
