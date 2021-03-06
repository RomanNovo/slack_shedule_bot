import logging
from fastapi.responses import Response
from fastapi import FastAPI, Request
import os
import re
import json

from slack_bolt.oauth import OAuthFlow
from slack_sdk.web.client import WebClient
import dbAdapter

from slack_bolt import App as Slack_App
from slack_bolt.adapter.fastapi import SlackRequestHandler

configFile = open("data/config.json",)
botConfig = json.load(configFile)
configFile.close()

oauth_flow=OAuthFlow.sqlite3(
        database="./data/lite.db",
        client_id=os.environ["SLACK_CLIENT_ID"],
        client_secret=os.environ["SLACK_CLIENT_SECRET"],
        installation_store_bot_only=True,
        scopes=[
            "app_mentions:read",
            "channels:history",
            "channels:read",
            "chat:write",
            "chat:write.customize",
            "chat:write.public",
            "groups:history",
            "groups:read",
            "im:history",
            "im:write",
            "incoming-webhook",
            "reminders:write",
            "reactions:write",
            "usergroups:read",
            "mpim:write",
            "channels:manage",
            "groups:write"
        ],
        token_rotation_expiration_minutes=60 * 24,  # for testing
    )

dbAdapter.checkDbSchema()

slack_app = Slack_App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    # token=os.environ["SECRET_TOKEN"],
    oauth_flow=oauth_flow
)


app_handler = SlackRequestHandler(slack_app)


# React to message
def placeReactionToMessage(client: WebClient, reaction, time_ts, channel):
    return client.reactions_add(channel=channel, name=reaction, timestamp=time_ts)

# Store message data to deta Base
def storeSheduledMessage(channel,team_id, obj, message_ts,  time):

    return dbAdapter.storeTask({
        "channel": channel,
        "team_id": team_id,
        "message_ts": message_ts,
        "getters": obj,
        "time": time
    })

# Return link to message
def getSlackUserMentions(text):
    matchesUsers = re.findall(r"(?:<@(\w+)>)", text)
    return matchesUsers


def getSlackUserGroupsMentions(text):
    matchesUsersGroups = re.findall(r"(?:<\!subteam\^(\w+)\|@\w+>)", text)
    return matchesUsersGroups


@slack_app.error
def custom_error_handler(error, body, response, logger, ack):
    ack(f"Error: {error}")
    logger.exception(f"Error: {error}")
    logger.info(f"Request body: {body}")

    return (f"Error: {error}")


@slack_app.event("app_mention")
def handle_mention(body, ack, say, logger, client):
    try:
        event = body["event"]
        ts = int(float(event["ts"]))
        sheduledTs = ts + botConfig["SECONDS_BEFORE_MENTION"]
        channel = event["channel"]
        team_id = event["team"]
        ownId = body["authorizations"][0]["user_id"]
        users = getSlackUserMentions(event["text"])
        groups = getSlackUserGroupsMentions(event["text"])
        users.remove(f"{ownId}")
        if len(groups) > 0 or len(users) > 0:
            # say(f"Groups {groups} and users {users} will be mentioned in 2 hours ")
            placeReactionToMessage(channel=channel, reaction=botConfig["REACTION_ACCEPT"], time_ts=event["ts"], client=client)
            storeSheduledMessage(
                channel, team_id, {"groups": groups, "users": users}, event["ts"], sheduledTs)
        else:
            say(botConfig["ERROR_USAGE"])
    except Exception as e:
        say("Error: " + str(e))


logger = logging.getLogger(__name__)
app = FastAPI()


@app.exception_handler(Exception)
def debug_exception_handler(request: Request, exc: Exception):
    import traceback
    return Response(
        content="".join(
            traceback.format_exception(
                etype=type(exc), value=exc, tb=exc.__traceback__
            )
        )
    )


@app.post("/slack/events")
async def endpoint(req: Request):
    if (req.headers.get("X-Slack-Retry-Reason")
            and req.headers.get("X-Slack-Retry-Num")):
        return "ok"
    print(f"req has completed")
    return await app_handler.handle(req)


@app.get("/slack/install")
async def endpoint(req: Request):
    return await app_handler.handle(req)


@app.get("/slack/oauth_redirect")
async def endpoint(req: Request):
    return await app_handler.handle(req)
