import enum
import re

from hare import food

class Level(object):
  def __init__(self, level_num, sequence, channel_name):
    super(Level, self).__setattr__('level_num', level_num)
    super(Level, self).__setattr__('sequence', tuple(food.GET_FOOD[x.lower()] for x in sequence))
    super(Level, self).__setattr__('channel_name', channel_name)

  def __repr__(self):
    return f'Level(level_num: {self.level_num}, sequence: {self.sequence}, channel_name: {self.channel_name})'

  def __setattr__(self, name, value):
    """ make Level immutable """
    raise AttributeError('could not set value')
  
  def __hash__(self):
    return hash((self.sequence, self.level_num))

LEVEL_CODES = (None, 'rrara', 'rkrr', 'akrkr', 'rre', 'ekkaek', 'ccaerce', 'cracker')
_AVAILABLE_FOODS_FOR_LEVEL = (None, 2, 3, 3, 4, 4, 5, 5)
ALL_LEVELS = frozenset(
    Level(i, LEVEL_CODES[i], f'hares-request-{i}')
    for i in range(1, len(LEVEL_CODES))
)
GET_LEVEL = {
    level.__getattribute__(attr): level
    for level in ALL_LEVELS
    for attr in ['level_num', 'channel_name']
}

def getFoodsInLevel(level=None):
  if level == None:
    return food.ALL_FOODS
  return food.ALL_FOODS[:_AVAILABLE_FOODS_FOR_LEVEL[level.level_num]]
