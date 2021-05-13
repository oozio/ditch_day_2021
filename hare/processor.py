import enum
import re

import discord_utils
from hare import food, level, mutation, peg

# From https://discord.com/developers/docs/topics/permissions#permissions
_VIEW_AND_USE_SLASH_COMMANDS = 0x0080000400
_NO_PERMISSIONS = 0x0000000000


def _getSingleFoodStringRegex(current_level=None):
   foods_string = '[{}]'.format(''.join([
       f.__getattribute__(attr)
       for f in level.getFoodsInLevel(current_level)
       for attr in ['character', 'emoji_unicode']
   ]))
   return rf'(?P<head>{foods_string})\s*(?P<tail>.*)'

def _processSequence(sequence, current_level=None):
  foods = []
  remaining = sequence.strip().lower()
  m = re.match(_getSingleFoodStringRegex(current_level), remaining)
  while m:
    foods.append(food.GET_FOOD[m.group('head')])
    remaining = m.group('tail')
    m = re.match(_getSingleFoodStringRegex(current_level), remaining)
  return tuple(foods)

def _processMutation(valid, reverse, index, mut, food_counts, f):
  m = mut(food_counts[f])
  if m == mutation.Mutation.NONE:
    # do nothing
    pass
  elif m == mutation.Mutation.REPLACE:
    valid[index][0] = f
  elif m == mutation.Mutation.UNION:
    valid[index].append(f)
  elif m == mutation.Mutation.DISAPPEAR:
    valid[index][0] = None
  elif m == mutation.Mutation.REVERSE:
    reverse[index] = True

def _getPegs(current_level, guess):
  n = len(guess)
  valid = [[f] for f in guess]
  food_counts = {f:0 for f in food.ALL_FOODS}
  reverse = [False] * n
  for i, f in enumerate(guess):
    if valid[i][0] != f:
      # base has been modified. do not process mutations
      continue
    _processMutation(valid, reverse, i - 1, f.mutate_left, food_counts, f)
    _processMutation(valid, reverse, i, f.mutate_center, food_counts, f)
    _processMutation(valid, reverse, (i + 1) % n, f.mutate_right, food_counts, f)
    food_counts[f] += 1

  sequence_food_counts = {f:0 for f in food.ALL_FOODS}
  valid_food_counts = {(f, r):0 for f in food.ALL_FOODS for r in [True, False]}
  correct_first_food_counts = {(f, r):0 for f in food.ALL_FOODS for r in [True, False]}
  correct_other_food_counts = {f:0 for f in food.ALL_FOODS}
  for i, f in enumerate(current_level.sequence):
    sequence_food_counts[f] += 1

    for j, f2 in enumerate(valid[i]):
      if f2 is None:
       continue
      valid_food_counts[f2, reverse[i]] += 1
      if f2 == f:
        if j == 0:
          correct_first_food_counts[f, reverse[i]] += 1
        else:
          correct_other_food_counts[f] += 1

  peg_counts = {p:0 for p in peg.Peg}
  for f in food.ALL_FOODS:
    solution = sequence_food_counts[f]
    guess = valid_food_counts[f, False]
    guess_inverted = valid_food_counts[f, True]
    right_position_inverted = correct_first_food_counts[f, True]
    right_position = correct_first_food_counts[f, False] +  correct_other_food_counts[f]

    peg_counts[peg.Peg.CORRECT] += right_position + max(guess_inverted - solution, 0)
    if solution > right_position:
      peg_counts[peg.Peg.MISPLACED] += min(solution, guess + guess_inverted)
      peg_counts[peg.Peg.MISPLACED] -= right_position + right_position_inverted

  peg_counts[peg.Peg.MISSING] = (len(current_level.sequence)
                               - peg_counts[peg.Peg.CORRECT]
                               - peg_counts[peg.Peg.MISPLACED])

  return peg_counts

def _getMessageAndProcessGuess(current_level, guess, server_id):
  if current_level.sequence != guess:
    return 'NO! WRONG!'
  next_level = level.GET_LEVEL.get(current_level.level_num + 1, None)
  if not next_level:
    return ('**Congrats! that\'s right!**\n' +
            '*You\'ve completed all the levels!*')
  next_level_foods = ''.join(str(f) for f in level.getFoodsInLevel(next_level))
  next_level_channel = discord_utils.get_channel(level.channel_name, server_id)
  everyone_id = server_id # @everyone has same role_id as server_id
  discord_utils.set_channel_permissions(everyone_id, next_level_channel['id'], _VIEW_AND_USE_SLASH_COMMANDS)
  return ('**Congrats! that\'s right!**\n' +
         f'*The next level will have {len(next_level.sequence)} foods.*\n' +
         f'*Types of foods in the next level: {next_level_foods}*')

def _getAvailableFoodsString(current_level):
  available_foods = level.getFoodsInLevel(current_level)
  available_foods_emojis = "".join(str(f) for f in available_foods)
  available_foods_characters = "".join(f.character for f in available_foods)
  return f'Available foods: {available_foods_emojis} ({available_foods_characters})'

def _processAdminCommandAndGetMessage(server_id, command):
  everyone_id = server_id # @everyone has same role_id as server_id
  if guess == 'start':
    for l in level.ALL_LEVELS:
      channel = discord_utils.get_channel(l.channel_name, server_id)
      discord_utils.set_channel_permissions(everyone_id,
                                            l.channel_name,
                                            _VIEW_AND_USE_SLASH_COMMANDS
                                                if l.level_num == 1
                                                else _NO_PERMISSIONS)
    return 'Hid all hare puzzle channels except level 1.'
  elif guess == 'reset':
    for l in level.ALL_LEVELS:
      channel = discord_utils.get_channel(l.channel_name, server_id)
      discord_utils.set_channel_permissions(everyone_id,
                                            l.channel_name,
                                            _NO_PERMISSIONS)
    return 'Hid all hare puzzle channels.'

  return 'Input either \"start\" or \"reset\"'

def evaluateInput(channel_id, guess):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  processed_level_code = _processSequence(level_code)
  channel_name = channel['name']
  if channel_name == 'admin-channel':
    return _processAdminCommandAndGetMessage(server_id, guess)
  current_level = level.GET_LEVEL.get(channel_name, None)
  if not current_level:
    # not hare puzzle channel
    return (f'Only call this from within one of the hare puzzle channels.')
  if not guess:
    # return current level info
    return (f'{_getAvailableFoodsString(current_level)}\n' +
            f'There are {len(current_level.sequence)} foods in this level.')
  if len(current_level.sequence) != len(guess):
    # wrong number of foods in guess
    return (f'{_getAvailableFoodsString(current_level)}\n' +
            f'Guess: {guess}\n' +
            f'Wrong number of foods. Try inputting {len(current_level.sequence)} foods for this level.')
  processed_guess = _processSequence(guess, current_level)
  if len(current_level.sequence) != len(processed_guess):
    return (f'{_getAvailableFoodsString(current_level)}\n' +
            f'Guess: {guess}\n' +
             'Invalid character. Please only include foods from the list of available foods.')
  pegs = _getPegs(current_level, processed_guess)
  message = _getMessageAndProcessGuess(current_level, processed_guess, server_id)
  return (f'{_getAvailableFoodsString(current_level)}\n' +
          f'Guess: {guess}\n' +
          f'{"".join(str(f) for f in processed_guess)}\n' +
          f'{"".join(p.value for p in [peg.Peg.CORRECT, peg.Peg.MISPLACED, peg.Peg.MISSING] for _ in range(pegs[p]))}\n' +
          f'{message}')
