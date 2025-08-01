#!/usr/bin/env bash

# Stop at first error
set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DOCKER_IMAGE_TAG="example-evaluation-track-2-atypical-mitosis-classification-preliminary-eval-phase"

docker build \
  --platform=linux/amd64 \
  --tag "$DOCKER_IMAGE_TAG"  \
  "$SCRIPT_DIR" 2>&1
