#!/bin/sh
# /etc/profile.d/unset-proxy.sh
# Unset proxy variables for all login shells if they are empty
for var in HTTP_PROXY HTTPS_PROXY http_proxy https_proxy NO_PROXY no_proxy; do
    eval "value=\${$var}"
    if [ -n "$value" ]; then
        unset "$var"
    fi
done
