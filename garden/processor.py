import re

from garden import calculator, critique
import discord_utils

_DISCUSSION_CHANNEL = 'garden-discussion'
_SIZE_50_ROLE_NAME = 'Size 50'
_GROW_SUBSTANCE = 'cake'
_SHRINK_SUBSTANCE = 'drink'

_CHANNEL_PATTERN = re.compile(r'garden-\d\d?')

def _processAdminCommandAndGetMessage(server_id, command):
  msg = []
  if command == 'reset' or command == 'start':
    all_users = discord_utils.get_all_users(server_id)
    for user in all_users:
      user_id = user['user']['id']
      for role in discord_utils.get_size_roles_for_user(server_id, user_id):
        discord_utils.remove_role(user_id, role['id'], server_id)
        print(f"Removed {role['id']} for {user_id}/{user}")
    msg.append('Removed all size roles.')

  if command == 'reset':
    everyone_id = server_id
    discord_utils.set_channel_permissions(everyone_id,
                                          _DISCUSSION_CHANNEL,
                                          server_id,
                                          'deny')
    msg.append('Hid garden-discussion channel.')

  if command == 'start':
    all_users = discord_utils.get_all_users(server_id)
    role_id = discord_utils.get_roles_by_names(server_id, [_SIZE_50_ROLE_NAME])[0]['id']
    for user in all_users:
      user_id = user['user']['id']
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

def evaluateInput(channel_id, user_id, substance, role_ids):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  if channel['name'] == 'admin-channel':
    return _processAdminCommandAndGetMessage(server_id, substance)
  if not _CHANNEL_PATTERN.match(channel['name']):
    return critique.getCritiqueOf(substance)

  if substance.lower() not in [_GROW_SUBSTANCE, _SHRINK_SUBSTANCE]:
    return f'You can\'t seem to find any "{substance}". There is only **{_GROW_SUBSTANCE}** and **{_SHRINK_SUBSTANCE}**.'

  roles = discord_utils.get_roles_by_ids(role_ids)
  if len(roles) == 0:
    # no size. Set size to 50 (should never occur)
    role_id = discord_utils.get_roles_by_names([_SIZE_50_ROLE_NAME])[0]['id']
    discord_utils.add_role(user_id, role_id, server_id)
    return

  # Pick first size. There should only be 1 size
  current_size_role = roles[0]
  m = discord_utils.SIZE_ROLE_NAME_PATTERN.match(current_size_role['name'])
  if not m:
    raise AssertionError('Size role does not have name in size format')
  current_size = m.group('size')
  if substance.lower() == _GROW_SUBSTANCE:
    new_size = calculator.grow(current_size)
  else:
    new_size = calculator.shrink(current_size)

  new_size_role = discord_utils.get_roles_by_names([f'Size {new_size}'])[0]
  for role in roles:
    discord_utils.remove_role(user_id, role['id'], server_id)
  discord_utils.add_role(user_id, new_size_role['id'], server_id)
