docker run -d \
  --name gospel-bot \
  --restart unless-stopped \
  -v ~/gospel-bot/data:/app/data \
  -v ~/gospel-bot/logs:/app/logs \
  -e BOT_TOKEN="7915703119:AAFMqfiFwYw6p-deMgrVghRBcXXtGKMCs8g" \
  -e ADMIN_USER_ID="2040516595" \
  -e OPENROUTER_API_KEY="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" \
  -e TZ="Europe/Moscow" \
  probedrik/gospel-bot:v2.5.1