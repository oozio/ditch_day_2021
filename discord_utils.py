import boto3
import re
import requests

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

RESPONSE_TYPES =  {
                    "PONG": 1,
                    "ACK_NO_SOURCE": 2,
                    "MESSAGE_NO_SOURCE": 3,
                    "MESSAGE_WITH_SOURCE": 4,
                    "ACK_WITH_SOURCE": 5
                  }

BASE_URL = "https://discord.com/api/v8"

ssm = boto3.client('ssm', region_name='us-east-2')

PUBLIC_KEY = ssm.get_parameter(Name="/discord/public_key", WithDecryption=True)['Parameter']['Value']
BOT_TOKEN = ssm.get_parameter(Name="/discord/bot_token", WithDecryption=True)['Parameter']['Value']
HEADERS = {
    "Authorization": f"Bot {BOT_TOKEN}",
    "Content-Type": "application/json"
}

SERVER_1 = '829131678839603270'
_CHANNEL_IDS_BY_NAME_AND_SERVER = {
    ('hare-puzzle-discussion', SERVER_1): '840727031984553984',
    ('hare-puzzle-level-1', SERVER_1): '841887525379112960',
    ('hare-puzzle-level-2', SERVER_1): '841887647051153429',
    ('hare-puzzle-level-3', SERVER_1): '841887669255667752',
    ('hare-puzzle-level-4', SERVER_1): '841887706212466688',
    ('hare-puzzle-level-5', SERVER_1): '841887729616551956',
    ('hare-puzzle-level-6', SERVER_1): '841887759336996864',
    ('hare-puzzle-level-7', SERVER_1): '841887780467507223',
    ('admin-channel', SERVER_1): '842265337747210240'
}

SIZE_ROLE_NAME_PATTERN = re.compile(r'Size (?P<size>\d+)')

_PERMISSIONS = {
    "VIEW_AND_USE_SLASH_COMMANDS": 0x0080000400,
    "ADD_REACTIONS": 0x0000000040,
    "USE_EXTERNAL_EMOJIS": 0x0000040000,
    "SEND_MESSAGES": 0x0000000800
}

def _form_permission():
    result = 0
    for permission in _PERMISSIONS.values():
        result = result | permission
    return result

_ROLES_CACHE = {}
def _get_all_roles(server_id):
    if server_id in _ROLES_CACHE:
        return _ROLES_CACHE[server_id]
    url = f"{BASE_URL}/guilds/{server_id}/roles"
    roles = requests.get(url, headers=HEADERS).json()
    _ROLES_CACHE[server_id] = roles
    return roles

def get_roles_by_ids(server_id, role_ids):
    roles = _get_all_roles(server_id)
    return [role for role in roles if role['id'] in role_ids]

def get_roles_by_names(server_id, role_names):
    roles = _get_all_roles(server_id):
    return [role for role in roles if role['name'] in role_names]

def _get_role_ids_by_name(server_id, role_names):
    results = {key: None for key in role_names}
    for role in _get_all_roles(server_id):
        if role['name'] in role_names:
            results[ role['name'] ] = role['id']
        if None not in results.values():
            return results

def _get_role_names_by_id(server_id, role_ids):
    results = {key: None for key in role_ids}
    for role in _get_all_roles(server_id):
        if role['id'] in role_ids:
            results[ role['id'] ] = role['name']
        if None not in results.values():
            return results

def remove_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    requests.delete(url, headers=HEADERS)

def add_role(user_id, role_id, server_id):
    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}/roles/{role_id}"
    requests.put(url, headers=HEADERS)

def get_size_role(server_id, roles):
    results = []
    role_names = _get_role_names_by_id(server_id, roles)
    for name in role_names.values():
        if SIZE_ROLE_NAME_PATTERN.match(name):
            results.append(name)
    if len(results) != 1:
        print(f"? {results}")
    return results[0]

def get_user_role_names(server_id, role_ids):
    return _get_role_names_by_id(server_id, role_ids)

def get_all_user_ids(server_id):
    # return all user_ids in a server

    # idk if this works? my bot is broken :(
    # https://discord.com/developers/docs/resources/guild#list-guild-members
    # url = f"{BASE_URL}/guilds/{server_id}/members"
    # return requests.get(url, json={'limit'=1000},  headers=HEADERS).json()
    pass

def get_size_roles_for_user(server_id, user_id):
    # return all role_ids that correspond to a Size role that a user has
    pass

def change_role(server_id, user_id, old_role_name, new_role_name):
    role_ids_by_name = _get_role_ids_by_name(server_id, [new_role_name, old_role_name])
    remove_role(user_id, role_ids_by_name[old_role_name], server_id)
    add_role(user_id, role_ids_by_name[new_role_name], server_id)

def get_channel_by_id(channel_id):
    """ Returns a channel object.

    returns channel object (dict).
    Params found at https://discord.com/developers/docs/resources/channel
    """
    url = f"https://discord.com/api/v8/channels/{channel_id}"
    return requests.get(url, headers=HEADERS).json()

def get_channel(channel_name, server_name):
    """ Returns a channel object.

    returns channel object (dict).
    Params found at https://discord.com/developers/docs/resources/channel
    """
    # TODO make this better??
    channel_id = _CHANNEL_IDS_BY_NAME_AND_SERVER[channel_name, server_name]
    return get_channel_by_id(channel_id)

def set_channel_permissions(role_id, channel_name, server_id, grant_type):
    """ Sets a channel's permissions for a given role.

    permissions found at https://discord.com/developers/docs/topics/permissions#permissions])
    """
    channel_id = _CHANNEL_IDS_BY_NAME_AND_SERVER[channel_name, server_id]
    permissions = _form_permission()

    put_body = {
        "type": 0, # roles
        grant_type: permissions
    }

    url = f"{BASE_URL}/channels/{channel_id}/permissions/{role_id}"

    requests.put(url, json=put_body, headers=HEADERS)

def move_user_to_channel(server_id, user_id, channel_name):
    # only works for voice channels
    body = {
        "channel_id": _CHANNEL_IDS_BY_NAME_AND_SERVER[channel_name, server_id]
    }

    url = f"{BASE_URL}/guilds/{server_id}/members/{user_id}"
    requests.patch(url, json=body, headers=HEADERS)

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
    for option in data.get('options', []):
        if option['name'] == target:
            return option['value']

def format_response(content, ephemeral, response_type=None):
    if response_type == 'PONG':
        return {
        "type": RESPONSE_TYPES[response_type] if response_type in RESPONSE_TYPES else RESPONSE_TYPES['MESSAGE_WITH_SOURCE'],
        }

    response = {
            "content": content,
            "embeds": [],
            "allowed_mentions": [],
            "flags": 64 if ephemeral else None
        }

    return response

def send_followup(application_id, interaction_token, content, ephemeral=False):
    body = format_response(content, ephemeral=ephemeral)
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}"
    requests.post(url, json=body, headers=HEADERS)

def update_response(application_id, interaction_token, content, ephemeral=False):
    body = format_response(content, ephemeral=ephemeral)
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.patch(url, json=body, headers=HEADERS)

def delete_response(application_id, interaction_token):
    url = f"{BASE_URL}/webhooks/{application_id}/{interaction_token}/messages/@original"
    requests.delete(url, headers=HEADERS)
