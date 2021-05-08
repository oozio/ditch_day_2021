import enum
import re

class Mutation(enum.Enum):
  NONE = 0
  REPLACE = 1
  UNION = 2
  DISAPPEAR = 3
  REVERSE = 4

  def __call__(self, instance):
    return self

class Peg(enum.Enum):
  MISSING = ':negative_squared_cross_mark:'
  MISPLACED = ':twisted_rightwards_arrows:'
  CORRECT = ':ballot_box_with_check:'

class Food(object):
  def __init__(self, emoji, character, mutate_left, mutate_center, mutate_right):
    super(Food, self).__setattr__("emoji", emoji)
    super(Food, self).__setattr__("character", character.lower())
    super(Food, self).__setattr__("mutate_left", mutate_left)
    super(Food, self).__setattr__("mutate_center", mutate_center)
    super(Food, self).__setattr__("mutate_right", mutate_right)

  def __repr__(self):
    return f'Food(emoji: "{self.emoji}", character: "{self.character}")'

  def __str__(self):
    return self.emoji

  def __setattr__(self, name, value):
    """ make Food immutable """
    raise AttributeError('could not set value')

  def __eq__(self, other):
    if other == None:
      return False
    return all(
        self.__getattribute__(attr) == other.__getattribute__(attr)
        for attr in ['emoji', 'character', 'mutate_left', 'mutate_center', 'mutate_right']
    )

  def __hash__(self):
    return hash((self.emoji, self.character))

AVOCADO = Food(
    ':avocado:',
    'a',
    Mutation.NONE,
    Mutation.DISAPPEAR,
    Mutation.NONE)
CHEESE = Food(
    ':cheese:',
    'c',
    Mutation.NONE,
    Mutation.NONE,
    Mutation.REPLACE)
EGG = Food(
    ':egg:',
    'e',
    Mutation.NONE,
    Mutation.REVERSE,
    Mutation.NONE)
KIWI = Food(
    ':kiwi:',
    'k',
    Mutation.UNION,
    Mutation.DISAPPEAR,
    Mutation.NONE)
RICE = Food(
    ':rice:',
    'r',
    Mutation.NONE,
    lambda i: Mutation.DISAPPEAR if i == 0 else Mutation.NONE,
    Mutation.NONE)
SALT = Food(
    ':salt:',
    's',
    Mutation.NONE,
    Mutation.NONE,
    Mutation.NONE)

ALL_FOODS = (SALT, AVOCADO, KIWI, EGG, CHEESE, RICE)
GET_FOOD = {
    food.__getattribute__(attr): food
    for food in ALL_FOODS
    for attr in ['emoji', 'character']
}

class Level(object):
  def __init__(self, level_num, sequence, access_code):
    super(Level, self).__setattr__('level_num', level_num)
    super(Level, self).__setattr__('sequence', tuple(GET_FOOD[x.lower()] for x in sequence))
    super(Level, self).__setattr__('access_code', tuple(GET_FOOD[x.lower()] for x in access_code))

  def __repr__(self):
    return f'Level(level_num: {self.level_num}, sequence: {self.sequence}, access_code: {self.access_code})'

  def __setattr__(self, name, value):
    """ make Level immutable """
    raise AttributeError('could not set value')
  
  def __hash__(self):
    return hash((self.sequence, self.level_num))

LEVEL_CODES = ('ssss', 'ssasa', 'asksk', 'kske', 'ceascec', 'kcrrsr', 'cracker')
ALL_LEVELS = frozenset([
    Level(i, LEVEL_CODES[i], LEVEL_CODES[i-1]) for i in range(1, 7)
])
GET_LEVEL = {
    level.__getattribute__(attr): level
    for level in ALL_LEVELS
    for attr in ['access_code']
}

def _getFoodsInLevel(level=None):
  if level == None:
    return ALL_FOODS
  return ALL_FOODS[:min(level.level_num + 1, 6)]

def _getSingleFoodStringRegex(level=None):
   foods_string = '[{}]'.format(''.join([f.character for f in _getFoodsInLevel(level)]))
   return rf'(?P<head>{foods_string})\s*(?P<tail>.*)'

def _processSequence(sequence, level=None):
  foods = []
  remaining = sequence.strip().lower()
  m = re.match(_getSingleFoodStringRegex(level), remaining)
  while m:
    foods.append(GET_FOOD[m.group('head')])
    remaining = m.group('tail')
    m = re.match(_getSingleFoodStringRegex(level), remaining)
  return tuple(foods)

def _processMutation(valid, reverse, index, mutation, food_counts, f):
  m = mutation(food_counts[f])
  if m == Mutation.NONE:
    # do nothing
    pass
  elif m == Mutation.REPLACE:
    valid[index][0] = f
  elif m == Mutation.UNION:
    valid[index].append(f)
  elif m == Mutation.DISAPPEAR:
    valid[index][0] = None
  elif m == Mutation.REVERSE:
    reverse[index] = True

def _getPegs(level, guess):
  n = len(guess)
  valid = [[f] for f in guess]
  food_counts = {f:0 for f in ALL_FOODS}
  reverse = [False] * n
  for i, f in enumerate(guess):
    if valid[i][0] != f:
      # base has been modified. do not process mutations
      continue
    _processMutation(valid, reverse, i - 1, f.mutate_left, food_counts, f)
    _processMutation(valid, reverse, i, f.mutate_center, food_counts, f)
    _processMutation(valid, reverse, (i + 1) % n, f.mutate_right, food_counts, f)
    food_counts[f] += 1

  sequence_food_counts = {f:0 for f in ALL_FOODS}
  valid_food_counts = {(f, r):0 for f in ALL_FOODS for r in [True, False]}
  correct_first_food_counts = {(f, r):0 for f in ALL_FOODS for r in [True, False]}
  correct_other_food_counts = {f:0 for f in ALL_FOODS}
  for i, f in enumerate(level.sequence):
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

  peg_counts = {p:0 for p in Peg}
  for f in ALL_FOODS:
    solution = sequence_food_counts[f]
    guess = valid_food_counts[f, False]
    guess_inverted = valid_food_counts[f, True]
    right_position_inverted = correct_first_food_counts[f, True]
    right_position = correct_first_food_counts[f, False] +  correct_other_food_counts[f]

    peg_counts[Peg.CORRECT] += right_position + max(guess_inverted - solution, 0)
    if solution > right_position:
      peg_counts[Peg.MISPLACED] += min(solution, guess + guess_inverted)
      peg_counts[Peg.MISPLACED] -= right_position + right_position_inverted
  
  peg_counts[Peg.MISSING] = len(level.sequence) - peg_counts[Peg.CORRECT] - peg_counts[Peg.MISPLACED]

  return [p for p in [Peg.CORRECT, Peg.MISPLACED, Peg.MISSING] for _ in range(peg_counts[p])]

def _getMessage(level, guess):
  if level.sequence != guess:
    return 'NO! WRONG!'
  next_level = GET_LEVEL.get(guess, None)
  if not next_level:
    return '**Congrats! that\'s right!**'
  next_level_foods = ''.join(str(f) for f in _getFoodsInLevel(next_level))
  return ('**Congrats! that\'s right!**\n' +
         f'*The next level will have {len(next_level.sequence)} foods.*\n' +
         f'*Types of foods in the next level: {next_level_foods}*')

def evaluateInput(level_code, guess):
  processed_level_code = _processSequence(level_code)
  level = GET_LEVEL.get(processed_level_code, None)
  if not level:
    return (f'Input (level): {level_code}\n' +
             'Invalid level code')
  processed_guess = _processSequence(guess, level)
  if len(level.sequence) != len(processed_guess):
    return (f'Level {level.level_num}: {level_code} - {"".join(str(f) for f in processed_level_code)}\n' + 
            f'Guess ({"".join(str(f) for f in _getFoodsInLevel(level))}): {guess} - {"".join(str(f) for f in processed_guess)}\n' +
            f'Wrong number of foods. Try inputting {len(level.sequence)} foods for this level.')
  pegs = _getPegs(level, processed_guess)
  message = _getMessage(level, processed_guess)
  return (f'Level {level.level_num}: {level_code} - {"".join(str(f) for f in processed_level_code)}\n' + 
          f'Guess ({"".join(str(f) for f in _getFoodsInLevel(level))}): {guess} - {"".join(str(f) for f in processed_guess)}\n' +
          f'{"".join(p.value for p in pegs)}\n'
          f'{message}')
