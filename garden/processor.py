import re

from garden import calculator, critique
import bunny_utils
import discord_utils

_DISCUSSION_CHANNEL = 'garden-discussion'
_SIZE_50_ROLE_NAME = 'Size 50'
_GROW_SUBSTANCE = 'cake'
_SHRINK_SUBSTANCE = 'drink'

_CHANNEL_PATTERN = re.compile(r'garden-(?P<room_number>\d\d?)')
_ADMIN_COMMAND_PATTERN = re.compile(r'(?P<command>start|reset)(?P<num_players>\d+)?')

_STARTING_BUNNIES = (50, 66, 41, 98, 18, 27, 73, 4)

def _processAdminCommandAndGetMessage(server_id, command):
  msg = []
  m = _ADMIN_COMMAND_PATTERN.match(command)
  if not m:
    return 'Input either "reset" or "start" followed by the number of players. e.g. "start5", "reset"'
  command = m.group('command')
  if command == 'start':
    try:
      num_players = int(m.group('num_players'))
    except TypeError as e:
      return 'Input either "reset" or "start" followed by the number of players. e.g. "start5", "reset"'
  if command == 'reset' or command == 'start':
    all_users = discord_utils.get_all_users(server_id)
    for user in all_users:
      user_id = user['user']['id']
      for role in discord_utils.get_size_roles_for_user(server_id, user_id):
        discord_utils.remove_role(user_id, role['id'], server_id)
        print(f"Removed {role['id']} for {user_id}/{user}")
    msg.append('Removed all size roles.')

    bunny_utils.exterminate()
    msg.append('Exterminated all mushrooms.')

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

    rooms = _STARTING_BUNNIES[:num_players]
    bunny_utils.populate_rooms(rooms)
    msg.append(f'Placed mushrooms in rooms: {" ".join(str(r) for r in rooms)}')

  return '\n'.join(msg)

def evaluateConsumeInput(channel_id, user_id, substance, role_ids):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  if channel['name'] == 'admin-channel':
    return _processAdminCommandAndGetMessage(server_id, substance)
  if not _CHANNEL_PATTERN.match(channel['name']):
    return critique.getCritiqueOf(substance)

  if bunny_utils.all_bunnies_are_caught():
    return f'There doesn\'t seem to be anything here to consume. All the {_GROW_SUBSTANCE} and {_SHRINK_SUBSTANCE} have been consumed.'
  if substance.lower() not in [_GROW_SUBSTANCE, _SHRINK_SUBSTANCE]:
    return f'You can\'t seem to find any "{substance}". There is only **{_GROW_SUBSTANCE}** and **{_SHRINK_SUBSTANCE}**.'

  size_roles = discord_utils.get_size_roles_for_user(server_id, user_id)
  if len(size_roles) == 0:
    # no size. Set size to 50 (should never occur)
    role_id = discord_utils.get_roles_by_names(server_id, [_SIZE_50_ROLE_NAME])[0]['id']
    discord_utils.add_role(user_id, role_id, server_id)
    return

  # Pick first size. There should only be 1 size
  current_size_role = size_roles[0]
  m = discord_utils.SIZE_ROLE_NAME_PATTERN.match(current_size_role['name'])
  if not m:
    raise AssertionError('Size role does not have name in size format')
  current_size = int(m.group('size'))
  if substance.lower() == _GROW_SUBSTANCE:
    new_size = calculator.grow(current_size)
  else:
    new_size = calculator.shrink(current_size)

  new_size_role = discord_utils.get_roles_by_names(server_id, [f'Size {new_size}'])[0]
  for role in size_roles:
    discord_utils.remove_role(user_id, role['id'], server_id)
  discord_utils.add_role(user_id, new_size_role['id'], server_id)

  if new_size > current_size:
    msg = f'The **{substance}** seems to make you grow from *Size {current_size}* to *Size {new_size}*.'
  elif new_size < current_size:
    msg = f'The **{substance}** seems to make you shrink from *Size {current_size}* to *Size {new_size}*.'
  else:
    return f'The **{substance}** you consumed seems to have no effect.'
  msg += '\nThe size change makes quite the ruckus.'
  
  caught_channel_nums = [b[bunny_utils.LOCATION] for b in bunny_utils.get_bunnies(status=bunny_utils.CAUGHT)]
  scampering_channel_nums = [b[bunny_utils.LOCATION] for b in bunny_utils.get_bunnies(status=bunny_utils.SCAMPERING)]
  bunny_utils.hide_all_bunnies()
  
  for n in scampering_channel_nums:
    channel = discord_utils.get_channel(f'garden-{n}', server_id)
    discord_utils.post_message_in_channel(channel['id'],
        'The mushroom has gone back into hiding. It seems to have gotten scared by a loud sound.')
    
  for n in caught_channel_nums:
    channel = discord_utils.get_channel(f'garden-{n}', server_id)
    discord_utils.post_message_in_channel(channel['id'],
        'The mushroom wriggles its way out of your arms and dashes back into hiding. It seems to have gotten scared by the loud sound.')

  return msg

def evaluateWhistleInput(channel_id):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  whistle_message_stem = 'You whistle a nice tune.'
  m = _CHANNEL_PATTERN.match(channel['name'])
  if not m or bunny_utils.all_bunnies_are_caught():
    return whistle_message_stem + ' Nothing seems to happen.'
  
  # Print mushroom messages to all mushroom channels
  channel_nums = [b[bunny_utils.LOCATION] for b in bunny_utils.get_bunnies(status=bunny_utils.HIDING)]
  mushroom_message = 'A mushroom came out of hiding. It seems to like the whistling.'
  if len(channel_nums) == 0:
    channel_nums = ([b[bunny_utils.LOCATION] for b in bunny_utils.get_bunnies(status=bunny_utils.CAUGHT)] +
                    [b[bunny_utils.LOCATION] for b in bunny_utils.get_bunnies(status=bunny_utils.SCAMPERING)])
    mushroom_message = 'The mushroom perks up. It seems to like the whistling.'
  else:
    bunny_utils.show_all_bunnies()
  
  for n in channel_nums:
    channel = discord_utils.get_channel(f'garden-{n}', server_id)
    discord_utils.post_message_in_channel(channel['id'], mushroom_message)
    
  # Print whistle response message to current channel
  current_garden = m.group('room_number')  
  if current_garden in channel_nums:
    return whistle_message_stem
  display = calculateNearestMushroom(current_garden, channel_nums)
  return whistle_message_stem + f' You hear some rustling over in garden-{display}.'

def calculateNearestMushroom(room_number, mushroom_channels):
  curr = int(room_number)
  return min((abs(int(n) - curr), int(n)) for n in mushroom_channels)[1]

def evaluateCatchInput(channel_id):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  m = _CHANNEL_PATTERN.match(channel['name'])
  if not m:
    return 'There doesn\'t seem to be anything to catch here.'
  room_number_str = m.group('room_number')
  all_scampering_bunnies = bunny_utils.get_bunnies(status=bunny_utils.SCAMPERING)
  if not any(b[bunny_utils.LOCATION] == room_number_str
             for b in all_scampering_bunnies):
    return 'There doesn\'t seem to be anything to catch here.'
  bunny_utils.catch_bunny(room_number_str)
  
  if bunny_utils.all_bunnies_are_caught():
    bunny_rooms = bunny_utils.get_bunnies()
    for n in bunny_rooms:
      channel = discord_utils.get_channel(f'garden-{n}', server_id)
      discord_utils.post_message_in_channel(channel['id'], 'All the mushrooms have been caught!')
  return 'You caught a mushroom!'
