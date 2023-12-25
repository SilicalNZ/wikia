#!/usr/bin/env bash

# THIS SCRIPT IS MADE TO BE CALLED FROM THE MAIN DIRECTORY
docker build --file ./services/discord/controllers/commands/import_category/main.dockerfile . --tag gcr.io/silical/wikia-discord-commands-import-category
docker push gcr.io/silical/wikia-discord-commands-import-category
gcloud run deploy wikia-discord-commands-import-category  \
  --execution-environment gen2 \
  --image gcr.io/silical/wikia-discord-commands-import-category \
  --region europe-west1 \
  --memory 512Mi \
  --max-instances 1
