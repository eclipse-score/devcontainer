#!/usr/bin/env bash
npm install -g @devcontainers/cli
pre-commit install

scripts/create_builder.sh
