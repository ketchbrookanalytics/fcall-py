FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Install Quarto (required by great-docs build)
RUN QUARTO_VERSION=$(curl -sSL https://api.github.com/repos/quarto-dev/quarto-cli/releases/latest \
      | jq -r '.tag_name | ltrimstr("v")') && \
    QUARTO_ARCH=$(dpkg --print-architecture) && \
    curl -fsSL "https://github.com/quarto-dev/quarto-cli/releases/download/v${QUARTO_VERSION}/quarto-${QUARTO_VERSION}-linux-${QUARTO_ARCH}.tar.gz" \
      | tar -xz -C /opt && \
    ln -s "/opt/quarto-${QUARTO_VERSION}/bin/quarto" /usr/local/bin/quarto

# Generate shell completion for the `vscode` user.
RUN uv generate-shell-completion bash >> /home/vscode/.bashrc
