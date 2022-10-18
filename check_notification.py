import os
import sys
import re
import shutil
import json
import requests
import boto3
import smtplib
import configparser
import logging
import traceback
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from atlassian import Confluence
from slack import WebClient
from pprint import pprint

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M')

def get_env(key, mandatory=False):
    if key in os.environ:
        if mandatory:
            if key not in os.environ:
                logging.error("Missing mandatory environment value: {0}".format(key))
                sys.exit(1)
        return os.environ.get(key).strip()
    return None


def get_slack_user_id(client, user):
    response = client.api_call(api_method='users.list')
    while True:
        if response.get("members"):
            for usr in response.get("members"):
                if usr.get("name").lower() == user.lower():
                    #logging.info(usr)
                    return usr.get("id")
        else:
            break

        if response.get("response_metadata") and response.get("response_metadata").get("next_cursor"):
            response = client.api_call(api_method='users.list?cursor=' + response.get("response_metadata").get("next_cursor"))
        else:
            break

    logging.error("User {0} not found".format(user))
    sys.exit(1)


def get_slack_channel_id(client, channel):

    # this is a workaround for Slack API bug
    channel_types = ["private_channel", "public_channel"]

    for channel_type in channel_types:
        response = client.api_call(
            api_method='conversations.list?exclude_archived=true&types={channel_type}'.format(
                channel_type=channel_type
            ))
        while True:
            if response.get("channels"):
                for chan in response.get("channels"):
                    if chan.get("name").lower() == channel.lower():
                        #logging.info(chan)
                        return chan.get("id")
            else:
                break

            if response.get("response_metadata") and response.get("response_metadata").get("next_cursor"):
                response = client.api_call(
                    api_method='conversations.list?exclude_archived=true&types={channel_type}&cursor={cursor}'.format(
                        channel_type=channel_type,
                        cursor=response.get("response_metadata").get("next_cursor")
                    ))
            else:
                break

    logging.error("Channel {0} not found".format(channel))
    sys.exit(1)



def delete_slack_message(client, channel, ts):
    try:
        if not client or not channel or not ts:
            logging.error("Missing parameter for deleting slack message client: {0} channel: {1} or ts: {2}".format(client, channel, ts))
            sys.exit(1)

        response = slack.chat_delete(
            channel=get_slack_channel_id(client, channel),
            ts=ts
        )
        logging.info(response)
        return response

    except Exception as e:
        logging.error(e)
        logging.error(traceback.print_exc())
        sys.exit(1)


def send_slack_message(client, channel = None, user = None, message = None, color = "#11A7D9"):

    try:
        if not client or not channel or not message:
            logging.error("Missing parameter for sending slack message client: {0} channel: {1} or message: {2}".format(client, channel, message))
            sys.exit(1)

        channel_id = get_slack_channel_id(client, channel)

        # send to user in the channel
        if user:
            user_id = get_slack_user_id(client, user)
            response = client.chat_postEphemeral(
                channel=channel_id,
                attachments=[{
                    "text": message,
                    "color": color
                }],
                user=user_id
            )
            logging.info(response)
            return response

        # send to channel
        response = client.chat_postMessage(
            channel=channel_id,
            attachments=[{
                "text": message,
                "color": color
            }]
        )
        logging.info(response)
        return response


    except Exception as e:
        logging.error(e)
        logging.error(traceback.print_exc())
        sys.exit(1)


def is_release():
    for arg in sys.argv:
        if arg.lower() == "--release":
            return True
    return False


def is_cleanup():
    for arg in sys.argv:
        if arg.lower() == "--cleanup":
            return True
    return False
