import enum

class Mutation(enum.Enum):
  NONE = 0
  REPLACE = 1
  UNION = 2
  DISAPPEAR = 3
  REVERSE = 4

  def __call__(self, instance):
    return self
