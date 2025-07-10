docker run -d \
  --name gospel-bot \
  --restart unless-stopped \
  -v ~/gospel-bot/data:/app/data \
  -v ~/gospel-bot/logs:/app/logs \
  -e BOT_TOKEN="7915703119:AAFMqfiFwYw6p-deMgrVghRBcXXtGKMCs8g" \
  -e ADMIN_USER_ID="2040516595" \
  -e OPENROUTER_API_KEY="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" \
  -e TZ="Europe/Moscow" \
  probedrik/gospel-bot:v2.5.0