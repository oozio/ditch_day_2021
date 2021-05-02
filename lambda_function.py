import json
import boto3

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from boto3.dynamodb.conditions import Key

import requests

ssm = boto3.client('ssm', region_name='us-east-2')

PUBLIC_KEY = ssm.get_parameter(Name="/discord/public_key", WithDecryption=True)['Parameter']['Value']
BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token", WithDecryption=True)['Parameter']['Value']

HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}
PING_PONG = {"type": 1}
RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }


def verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
    
    message = auth_ts.encode() + raw_body.encode()
    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    verify_key.verify(message, bytes.fromhex(auth_sig))

def ping_pong(body):
    if body.get("type") == 1:
        return True
    return False

def get_messages(channel_id, limit, specified_message):
    url = f"https://discord.com/api/v8/channels/{channel_id}/messages?limit={limit}"
    ind_url = f"https://discord.com/api/v8/channels/{channel_id}/messages/{specified_message}"
    messages = requests.get(url, headers=HEADERS).json()
    if specified_message:
        messages.append(requests.get(ind_url, headers=HEADERS).json())
        
    return messages

def get_images(messages):
    results = []
    for message in messages:
        message_id = message['id']
        if message['attachments']:
            for attachment in message['attachments']:
                image_url = message['attachments'][0]['url']
                if '.jpg' in image_url or '.jpeg' in image_url or '.png' in image_url:
                    results.append({'id': message_id, 'image_url': image_url})
        elif message['embeds']:
            for embed in message['embeds']:
                if embed['type'] == 'image':
                    image_url = embed['url'].split("?")[0]
                    results.append({'id': message_id, 'image_url': image_url})
    
    return results

def format_response(response_type, content, tts=False):
    return {
        "type": RESPONSE_TYPES[response_type] if response_type in RESPONSE_TYPES else RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
        "data": {
            "tts": tts,
            "content": content,
            "embeds": [],
            "allowed_mentions": []
            }
        }


def lambda_handler(event, context):
    print(event)
    try:
        verify_signature(event)
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

    body = event.get('body-json')
    if ping_pong(body):
        return PING_PONG
    
    data = body["data"]
    channel_id = body["channel_id"]

    if data['name'] == "blep":
        return format_response('MESSAGE_WITH_SOURCE', "blep blep")

    return format_response('MESSAGE_WITH_SOURCE', "what!!!")
