_CRITIQUES = (
  'It tastes sour.',
  'It tastes bitter.',
  'It tastes sweet.',
  'It\'s thick and a bit salty.',
  'It tastes spicy.',
  'It tastes like you would expect.',
  'It tastes like regret.',
  'It tastes like nothing.',
  'It tastes like booze.',
  'It tastes like feet.',
  'It\'s possibly the best thing you\'ve ever tasted.',
  'It\'s possibly the worst thing you\'ve ever tasted.',
  'The texture is offputting.',
  'It burns the back of your mouth.',
  'It\'s physically hard to swallow.',
  'Just thinking about makes you want to gag.',
  'It tastes like medicine. Ew...',
  'Cardboard has more flavor than this.',
  'It\'s surprisingly crunchy.',
  'It\'s a salty surprise.',
)
_NUM_CRITIQUES = len(_CRITIQUES)

def getCritiqueOf(substance):
  critique = _CRITIQUES[hash(substance) % _NUM_CRITIQUES]
  return f'You consume **{substance}**. {critique}'
