#!/usr/bin/env bash
npm install -g @devcontainers/cli
pre-commit install

scripts/create_builder.sh

sudo apt-get update && sudo apt-get install -y shellcheck
