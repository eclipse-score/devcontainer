#!/usr/bin/env bash

# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-FileCopyrightText: 2026 Contributors to the Eclipse Foundation
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************

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
