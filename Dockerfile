ARG BASE_IMAGE=senzing/senzing-base:1.6.2
FROM ${BASE_IMAGE}

ENV REFRESHED_AT=2021-10-11

LABEL Name="senzing/template" \
      Maintainer="support@senzing.com" \
      Version="1.2.1"

HEALTHCHECK CMD ["/app/healthcheck.sh"]

# Run as "root" for system installation.

USER root

# Install packages via apt.

# Copy files from repository.

COPY ./rootfs /

# Make non-root container.

USER 1001

# Runtime execution.

WORKDIR /app
CMD ["/app/sleep-infinity.sh"]
