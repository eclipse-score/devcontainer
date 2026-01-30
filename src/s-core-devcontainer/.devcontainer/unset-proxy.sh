#!/bin/bash
# /etc/profile.d/unset-proxy.sh
# Unset proxy variables for all login shells if they are empty
for var in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy; do
    if [ -z "${!var}" ]; then
        unset "${var}"
    fi
done
