#!/bin/bash
##
## Copyright 2023 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##

# Fail fast if any command fails
set -e

# Wait for contracts if needed
if [ "${DEPLOY_CONTRACTS}" = "true" ]; then
  while [ ! -f "/ocean-contracts/artifacts/ready" ]; do
    sleep 2
  done
fi

# Copy artifacts if they exist
/bin/cp -up /ocean-provider/artifacts/* /usr/local/artifacts/ 2>/dev/null || true

gunicorn \
  -b "${OCEAN_PROVIDER_URL#*://}" \
  -w "${OCEAN_PROVIDER_WORKERS}" \
  -t "${OCEAN_PROVIDER_TIMEOUT}" \
  ocean_provider.run:app
