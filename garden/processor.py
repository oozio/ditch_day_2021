import re

from garden import critique
import discord_utils

_DISCUSSION_CHANNEL = 'garden-discussion'

_CHANNEL_PATTERN = re.compile(r'garden-\d\d?')

def _processAdminCommandAndGetMessage(server_id, command):
  msg = []
  if command == 'reset' or command == 'start':
    all_user_ids = discord_utils.get_all_user_ids(server_id)
    for user_id in all_user_ids:
      for role_id in discord_utils.get_size_roles_for_user(server_id, user_id):
        discord_utils.remove_role(user_id, role_id, server_id)
    msg.append('Removed all size roles.')

  if command == 'reset':
    everyone_id = server_id
    discord_utils.set_channel_permissions(everyone_id,
                                          _DISCUSSION_CHANNEL,
                                          server_id,
                                          'deny')
    msg.append('Hid garden-discussion channel.')

  if command == 'start':
    all_user_ids = discord_utils.get_all_user_ids(server_id)
    role_id = 'Size 50'
    for user_id in all_user_ids:
      discord_utils.add_role(user_id, role_id, server_id)
    msg.append('Set all sizes to 50.')

    everyone_id = server_id
    discord_utils.set_channel_permissions(everyone_id,
                                          _DISCUSSION_CHANNEL,
                                          server_id,
                                          'allow')
    msg.append('Enabled garden-discussion channel')

  if msg:
    return '\n'.join(msg)
  return 'Input either \"start\" or \"reset\"'

def evaluateInput(channel_id, user_id, substance):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  if channel['name'] == 'admin-channel':
    return _processAdminCommandAndGetMessage(server_id, substance)
  if not _CHANNEL_PATTERN.match(channel['name']):
    return critique.getCritiqueOf(substance)

  # TODO add processing for puzzle
