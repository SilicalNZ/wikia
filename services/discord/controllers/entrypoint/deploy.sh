#!/usr/bin/env bash

# THIS SCRIPT IS MADE TO BE CALLED FROM THE MAIN DIRECTORY
docker build --file ./services/discord/controllers/entrypoint/main.dockerfile . --tag gcr.io/silical/wikia-discord-entrypoint
docker push gcr.io/silical/wikia-discord-entrypoint
gcloud run deploy wikia-discord-entrypoint \
  --execution-environment gen2 \
  --image gcr.io/silical/wikia-discord-entrypoint \
  --allow-unauthenticated \
  --region europe-west1 \
  --memory 512Mi \
  --max-instances 1

