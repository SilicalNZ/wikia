#-- Build base image ---------------------------------------------------------------------------------------------------
FROM golang:1.18-buster AS dependency_solving_environment

# Workdir
WORKDIR /opt/src/project

# Copy project code
COPY ./services/discord/controllers/entrypoint ./services/discord/controllers/entrypoint

# Build the binary.

WORKDIR /opt/src/project/services/discord/controllers/entrypoint/

RUN go build -o server ./main.go

# Use the official Debian slim image for a lean production container.
# https://hub.docker.com/_/debian
# https://docs.docker.com/develop/develop-images/multistage-build/#use-multi-stage-builds
FROM debian:buster-slim
RUN set -x && apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*
# Copy the binary to the production image from the builder stage.
COPY --from=dependency_solving_environment /opt/src/project/services/discord/controllers/entrypoint/server /

# Env
ENV is_prod true
ENV DISCORD_PUBLIC_KEY 0d884f73ba713b6c1dff96f139e4ee764f22fd5ff314b07ee4e67042524aeefc
ENV CLOUD_PROJECT_ID silical

# Run the web service on container startup.
CMD ["./server"]
