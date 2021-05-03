import boto3

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

RESPONSE_TYPES =  { 
                    "PONG": 1, 
                    "ACK_NO_SOURCE": 2, 
                    "MESSAGE_NO_SOURCE": 3, 
                    "MESSAGE_WITH_SOURCE": 4, 
                    "ACK_WITH_SOURCE": 5
                  }


ssm = boto3.client('ssm', region_name='us-east-2')

PUBLIC_KEY = ssm.get_parameter(Name="/discord/public_key", WithDecryption=True)['Parameter']['Value']
BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token", WithDecryption=True)['Parameter']['Value']
HEADERS = {"Authorization": f"Bot {BOT_TOKEN}"}


def get_messages(channel_id, limit, specified_message):
    # gets the last <limit> messages from the specified channel, and appends any message specified by id
    # doesn't check if <specified_message> is duplicated
    url = f"https://discord.com/api/v8/channels/{channel_id}/messages?limit={limit}"
    ind_url = f"https://discord.com/api/v8/channels/{channel_id}/messages/{specified_message}"
    messages = requests.get(url, headers=HEADERS).json()
    if specified_message:
        messages.append(requests.get(ind_url, headers=HEADERS).json())
        
    return messages

def _verify_signature(event):
    raw_body = event.get("rawBody")
    auth_sig = event['params']['header'].get('x-signature-ed25519')
    auth_ts  = event['params']['header'].get('x-signature-timestamp')
    message = auth_ts.encode() + raw_body.encode()
    
    try:
        verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        verify_key.verify(message, bytes.fromhex(auth_sig))
    except Exception as e:
        raise Exception(f"[UNAUTHORIZED] Invalid request signature: {e}")

def _ping_pong(body):
    if body.get("type") == 1:
        return True
    return False
    
def check_input(event):
    _verify_signature(event)
    body = event.get('body-json')
    if _ping_pong(body):
        return format_response("PONG", None)

def get_input(data, target):
    for option in data['options']:
        if option['name'] == target:
            return option['value']

    
def format_response(response_type, content, tts=False):
    response = {
        "type": RESPONSE_TYPES[response_type] if response_type in RESPONSE_TYPES else RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
        }
    if response_type != 'PONG':
        response["data"] = {
            "tts": tts,
            "content": content,
            "embeds": [],
            "allowed_mentions": []
            }
    return response

