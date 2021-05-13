import enum
import re

from hare import mutation

class Food(object):
  def __init__(self, emoji, emoji_unicode, character, mutate_left, mutate_center, mutate_right):
    super(Food, self).__setattr__("emoji", emoji)
    super(Food, self).__setattr__("emoji_unicode", emoji_unicode)
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
        for attr in ['emoji',
                     'emoji_unicode',
                     'character',
                     'mutate_left',
                     'mutate_center',
                     'mutate_right']
    )

  def __hash__(self):
    return hash((self.emoji, self.emoji_unicode, self.character))

AVOCADO = Food(
    ':avocado:',
    b'\xf0\x9f\xa5\x91'.decode(),
    'a',
    mutation.Mutation.NONE,
    mutation.Mutation.DISAPPEAR,
    mutation.Mutation.NONE)
CHEESE = Food(
    ':cheese:',
    b'\xf0\x9f\xa7\x80'.decode(),
    'c',
    mutation.Mutation.NONE,
    mutation.Mutation.NONE,
    mutation.Mutation.REPLACE)
EGG = Food(
    ':egg:',
    b'\xf0\x9f\xa5\x9a'.decode(),
    'e',
    mutation.Mutation.NONE,
    mutation.Mutation.REVERSE,
    mutation.Mutation.NONE)
KIWI = Food(
    ':kiwi:',
    b'\xf0\x9f\xa5\x9d'.decode(),
    'k',
    mutation.Mutation.UNION,
    mutation.Mutation.DISAPPEAR,
    mutation.Mutation.NONE)
RICE = Food(
    ':rice:',
    b'\xf0\x9f\x8d\x9a'.decode(),
    'r',
    mutation.Mutation.NONE,
    mutation.Mutation.NONE,
    mutation.Mutation.NONE)

ALL_FOODS = (RICE, AVOCADO, KIWI, EGG, CHEESE)
GET_FOOD = {
    food.__getattribute__(attr): food
    for food in ALL_FOODS
    for attr in ['emoji', 'character']
}
