
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

from main import slack_app, botConfig



client_id = os.environ["SLACK_CLIENT_ID"]
client_secret = os.environ["SLACK_CLIENT_SECRET"]
signing_secret = os.environ["SLACK_SIGNING_SECRET"]

rotator = TokenRotator(
    client_secret=client_secret,
    client_id=client_id,
)
client = WebClient()

client.retry_handlers


def getMessageLink(client: WebClient, channel, ts, team_id):
    try:
        res = client.chat_getPermalink(token=getLatestToken(team_id),
         channel=channel, message_ts="{:.6f}".format(float(ts)))
        if res.data["ok"]:
            return res.data["permalink"]
    except Exception as err:
        print("permalink " + str(err))
        pass
    return ""

# Return list of group users


def getSlackGroupUsers(client: WebClient, groupId,team_id):
    groupResult = client.usergroups_users_list(
        token=getLatestToken(team_id), usergroup=groupId)
    if groupResult.data["ok"]:
        return groupResult.data["users"]
    else:
        return []


def getBotData(team_id):
    bot: Bot = slack_app.installation_store.find_bot(
        team_id=team_id, enterprise_id="")
    newBot: Bot = rotator.perform_bot_token_rotation(
        bot=bot, minutes_before_expiration=20)
    if newBot:
        bot = newBot
        slack_app.installation_store.save_bot(bot)
    return bot


def getLatestToken(team_id):
    bot = getBotData(team_id)
    return bot.bot_token


def performTask(client: WebClient, msg):
    users = msg["getters"]["users"]
    groups = msg["getters"]["groups"]
    team_id = msg["team_id"]
    channelName = msg["channel"]
    messageTs = str(msg["message_ts"]).replace(',', '.')
    for group in groups:
        users += getSlackGroupUsers(client, group, team_id)
    users = list(set(users))
    print(f"{users} gonna be mentioned")
    msgLink = getMessageLink(client, channelName, messageTs, team_id)
    for user in users:
        convRes = client.conversations_open(token=getLatestToken(team_id), users=user)
        if convRes.data["ok"]:
            chatId = convRes.data["channel"]["id"]
            text = botConfig["MENTION_MESSAGE"] + f" <#{channelName}>"
            if msgLink:
                text += f"  <{msgLink}|сообщение>"
            result = client.chat_postMessage(
                token=getLatestToken(team_id),
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
        team_id = msg["team_id"]
        bot = getBotData(team_id)
        client = WebClient()
        client.token = bot.bot_token
        try:
            performTask(client, msg)
        except Exception as e:
            print(str(e))

    return result

proceed()
