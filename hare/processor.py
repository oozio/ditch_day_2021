import enum
import re

from . import food
from . import level
from . import mutation
from . import peg

def _getSingleFoodStringRegex(current_level=None):
   foods_string = '[{}]'.format(''.join([f.character for f in level.getFoodsInLevel(current_level)]))
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

def _getMessage(current_level, guess):
  if current_level.sequence != guess:
    return 'NO! WRONG!'
  next_level = level.GET_LEVEL.get(guess, None)
  if not next_level:
    return ('**Congrats! that\'s right!**\n' +
            '*You\'ve completed all the levels!*')
  next_level_foods = ''.join(str(f) for f in level.getFoodsInLevel(next_level))
  return ('**Congrats! that\'s right!**\n' +
         f'*Use this as the next level code.*\n' +
         f'*The next level will have {len(next_level.sequence)} foods.*\n' +
         f'*Types of foods in the next level: {next_level_foods}*')

def evaluateInput(level_code, guess):
  processed_level_code = _processSequence(level_code)
  current_level = level.GET_LEVEL.get(processed_level_code, None)
  if not current_level:
    return (f'Input (level): {level_code}\n' +
             'Invalid level code')
  if not guess:
    # return all level codes up to current level
    level_nums = range(1, current_level.level_num + 1)
    level_codes = [_processSequence(level.LEVEL_CODES[i]) for i in range(current_level.level_num)]
    readable_level_codes = '\n'.join(
        f'Level {level_nums[i]}: {"".join(str(f) for f in level_codes[i])} ({"".join(f.character for f in level_codes[i])})'
        if i < current_level.level_num else
        f'Level {i + 1}: *UNKNOWN*'
        for i in range(len(level.ALL_LEVELS))
    )
    return ('Level codes:\n' +
           f'{readable_level_codes}')
  if len(current_level.sequence) != len(guess):
    return (f'Level {current_level.level_num} / {len(level.ALL_LEVELS)}: {level_code} - Available Foods: {"".join(str(f) for f in level.getFoodsInLevel(current_level))}\n' + 
            f'Guess: {guess}\n' +
            f'Wrong number of foods. Try inputting {len(current_level.sequence)} foods for this level.')
  processed_guess = _processSequence(guess, current_level)
  if len(current_level.sequence) != len(processed_guess):
    return (f'Level {current_level.level_num} / {len(level.ALL_LEVELS)}: {level_code} - Available Foods: {"".join(str(f) for f in level.getFoodsInLevel(current_level))}\n' + 
            f'Guess: {guess}\n' +
             'Invalid character. Please only include foods from the list of available foods.')
  pegs = _getPegs(current_level, processed_guess)
  message = _getMessage(current_level, processed_guess)
  return (f'Level {current_level.level_num} / {len(level.ALL_LEVELS)} : {level_code} - Available Foods: {"".join(str(f) for f in level.getFoodsInLevel(current_level))}\n' + 
          f'Guess: {guess}\n' +
          f'{"".join(str(f) for f in processed_guess)}\n' +
          f'{"".join(p.value for p in [peg.Peg.CORRECT, peg.Peg.MISPLACED, peg.Peg.MISSING] for _ in range(pegs[p]))}\n' +
          f'{message}')
