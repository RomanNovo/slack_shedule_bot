## Slack Shedule Bot

Sends new users a direct message after some time from them mentioned.

### Configuration and Deployment

Fill the .env file like .env.example

Open port on docker-compose

Create slack app from manifest example

Requires the following oauth permissions in your slack app.

- `app_mentions:read`
- `channels:history`
- `channels:read`
- `channels:manage`
- `chat:write`
- `chat:write.customize`
- `chat:write.public`
- `commands`
- `groups:history`
- `groups:read`
- `im:history`
- `incoming-webhook`
- `usergroups:read`
- `reminders:write`
- `mpim:write`
- `im:write`

