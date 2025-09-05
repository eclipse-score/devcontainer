#!/usr/bin/env bash
set -eo pipefail

USERNAME=$(whoami)
GROUPNAME=$(id -gn)
COMMANDHISTORY_DIR="/commandhistory"
BASH_HISTORY_FILE="${COMMANDHISTORY_DIR}/.bash_history"
SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=${BASH_HISTORY_FILE}"
BASHRC_FILE="${HOME}/.bashrc"

# Ensure the directory exists and set permissions
sudo mkdir -p "${COMMANDHISTORY_DIR}"
sudo chown "${USERNAME}:${GROUPNAME}" "${COMMANDHISTORY_DIR}"
sudo chmod 755 "${COMMANDHISTORY_DIR}"

# Create .bash_history file if it doesn't exist and set permissions
if [[ ! -f "${BASH_HISTORY_FILE}" ]]; then
    touch "${BASH_HISTORY_FILE}"
    sudo chown "${USERNAME}:${GROUPNAME}" "${BASH_HISTORY_FILE}"
    sudo chmod 600 "${BASH_HISTORY_FILE}"
fi

# Add snippet to .bashrc if not already present
grep -qF -- "${SNIPPET}" "${BASHRC_FILE}" || echo "${SNIPPET}" >> "${BASHRC_FILE}"
