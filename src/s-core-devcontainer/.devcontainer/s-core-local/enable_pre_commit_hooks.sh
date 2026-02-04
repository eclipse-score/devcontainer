#!/usr/bin/env bash

PRE_COMMIT_CONFIG_FILE=".pre-commit-config.yaml"

if [[ -f "${PRE_COMMIT_CONFIG_FILE}" ]]
then
    echo "Pre-commit configuration found (${PRE_COMMIT_CONFIG_FILE})"
    "${PIPX_BIN_DIR}/pre-commit" install
else
    echo "No pre-commit configuration found (${PRE_COMMIT_CONFIG_FILE})"
    echo "Skipping pre-commit hook's installation"
fi
