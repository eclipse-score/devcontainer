FROM buildpack-deps:noble-curl

# Proxy arguments for build-time network access
ARG HTTP_PROXY=""
ARG HTTPS_PROXY=""
ARG http_proxy=""
ARG https_proxy=""
ARG NO_PROXY=""
ARG no_proxy=""

# Set proxy environment variables for the build process
ENV HTTP_PROXY=${HTTP_PROXY}
ENV HTTPS_PROXY=${HTTPS_PROXY}
ENV http_proxy=${http_proxy}
ENV https_proxy=${https_proxy}
ENV NO_PROXY=${NO_PROXY}
ENV no_proxy=${no_proxy}

LABEL dev.containers.features="common"

# Unset proxy variables for all login shells
COPY unset-proxy.sh /etc/profile.d/unset-proxy.sh

RUN userdel -f -r ubuntu
