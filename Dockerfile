##
## Copyright 2023 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##
# ===== Builder Stage =====
FROM python:3.8-bookworm AS builder

ENV PYTHONUNBUFFERED=1
WORKDIR /ocean-provider

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables at the front of the PATH
ENV PATH="/ocean-provider/.venv/bin:$PATH"

# Compile bytecode
ENV UV_COMPILE_BYTECODE=1

# Copy only dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Copy the full source code
COPY . .

# ===== Runtime Stage =====
FROM python:3.8-slim-bookworm

WORKDIR /ocean-provider

# Copy the virtual environment and source code
COPY --from=builder /ocean-provider/ /ocean-provider/

# Environment variables
ENV PATH="/ocean-provider/.venv/bin:$PATH" \
    NETWORK_URL='http://127.0.0.1:8545' \
    PROVIDER_PRIVATE_KEY='' \
    PROVIDER_ADDRESS='' \
    AZURE_ACCOUNT_NAME='' \
    AZURE_ACCOUNT_KEY='' \
    AZURE_RESOURCE_GROUP='' \
    AZURE_LOCATION='' \
    AZURE_CLIENT_ID='' \
    AZURE_CLIENT_SECRET='' \
    AZURE_TENANT_ID='' \
    AZURE_SUBSCRIPTION_ID='' \
    MAX_CHECKSUM_LENGTH='5242880' \
    AZURE_SHARE_INPUT='compute' \
    AZURE_SHARE_OUTPUT='output' \
    OCEAN_PROVIDER_URL='http://0.0.0.0:8030' \
    OCEAN_PROVIDER_WORKERS='1' \
    OCEAN_PROVIDER_TIMEOUT='9000' \
    ALLOW_NON_PUBLIC_IP=False \
    ARWEAVE_GATEWAY=https://arweave.net/ \
    IPFS_GATEWAY=https://ipfs.io \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ENTRYPOINT ["/ocean-provider/docker-entrypoint.sh"]

EXPOSE 8030