
from slack_sdk.http_retry.builtin_handlers import RateLimitErrorRetryHandler
from slack_sdk.oauth.installation_store.models.bot import Bot
from slack_sdk.oauth.installation_store.models.installation import Installation
from slack_sdk.oauth.token_rotation.rotator import TokenRotator
from slack_sdk.web.client import WebClient
import dbAdapter
import datetime
import os

from dotenv import load_dotenv
load_dotenv(dotenv_path="/app/.env")

from main import slack_app



client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]

rotator = TokenRotator(
    client_secret=client_secret,
    client_id=client_id,
)
client = WebClient()

client.retry_handlers


def getMessageLink(client: WebClient, channel, ts):
    try:
        res = client.chat_getPermalink(token=getLatestToken(
        ), channel=channel, message_ts="{:.6f}".format(float(ts)))
        if res.data["ok"]:
            return res.data["permalink"]
    except Exception as err:
        print("permalink " + str(err))
        pass
    return ""

# Return list of group users


def getSlackGroupUsers(client: WebClient, groupId):
    groupResult = client.usergroups_users_list(
        token=getLatestToken(), usergroup=groupId)
    if groupResult.data["ok"]:
        return groupResult.data["users"]
    else:
        return []


def getBotData():
    bot: Bot = slack_app.installation_store.find_bot(
        team_id="T02FV5FP1DL", enterprise_id="")
    newBot: Bot = rotator.perform_bot_token_rotation(
        bot=bot, minutes_before_expiration=20)
    if newBot:
        bot = newBot
        slack_app.installation_store.save_bot(bot)
    return bot


def getLatestToken():
    bot = getBotData()
    return bot.bot_token


def performTask(client: WebClient, msg):
    users = msg["getters"]["users"]
    groups = msg["getters"]["groups"]
    channelName = msg["channel"]
    messageTs = str(msg["message_ts"]).replace(',', '.')
    for group in groups:
        users += getSlackGroupUsers(client, group)
    users = list(set(users))
    print(f"{users} gonna be mentioned")
    msgLink = getMessageLink(client, channelName, messageTs)
    for user in users:
        convRes = client.conversations_open(token=getLatestToken(), users=user)
        if convRes.data["ok"]:
            chatId = convRes.data["channel"]["id"]
            text = f"You has been mentioned in <#{channelName}>"
            if msgLink:
                text += f" at <{msgLink}>"
            result = client.chat_postMessage(
                token=getLatestToken(),
                channel=chatId,
                text=text)
            if result["ok"]:
                key = msg["id"]
                dbAdapter.markTaskAsDone(key)
                print(f"Task {key} has completed. {user} mentioned")
            else:
                print(f"Task {key} has error")
        else:
            pass


def proceed():
    ts_now = datetime.datetime.now().timestamp()
    msgs = dbAdapter.getTaskOlderTs(ts_now)

    result = ""
    for msg in msgs:
        bot = getBotData()
        client = WebClient()
        client.token = bot.bot_token
        try:
            performTask(client, msg)
        except Exception as e:
            print(str(e))

    return result

proceed()
