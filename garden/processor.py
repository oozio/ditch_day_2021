import re

import discord_utils

_CHANNEL_PATTERN = re.compile(r'garden-\d\d?')

def _processAdminCommandAndGetMessage(server_id, command):
  if command == 'start':
    # TODO set all roles to size 50
    return 'Set all sizes to 50.'
  if command == 'reset':
    # TODO remove all size roles
    return 'Removed all size roles.'
  return 'Input either \"start\" or \"reset\"'

def evaluateInput(channel_id, user_id, substance):
  channel = discord_utils.get_channel_by_id(channel_id)
  if channel['name'] == 'admin-channel':
    return _processAdminCommandAndGetMessage(server_id, substance)
  if not _CHANNEL_PATTERN.match(channel['name']):
    return f'You eat **{substance}**. It tastes like you would expect.'
  # TODO add processing for puzzle
