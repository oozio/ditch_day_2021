import re

import discord_utils

class Time(object):
  _TIME_PATTERN_STANDARD = re.compile(r'(?P<hour>\d?\d):(?P<minute>\d\d)')
  _TIME_PATTERN_NOCOLON = re.compile(r'(?P<hour>\d?\d)(?P<minute>\d\d)')
  _TIME_PATTERN_MINUTE = re.compile(r'(?P<minute>\d?\d)')

  def __init__(self, standard, minute):
    super(Time, self).__setattr__("standard", standard)
    super(Time, self).__setattr__("minute", minute)

  def _getStandardFormat(hour, minute):
    hour = int(hour)
    minute = int(minute)
    if hour == 0:
      hour = 12
    minute = str(minute)
    if len(minute) < 2:
      minute = '0' + minute
    return f'{hour}:{minute}'

  def _getMinuteFormat(hour, minute):
    return (int(hour) * 60 + int(minute)) % 720

  def _timeByHourAndMinute(hour, minute):
    return Time(Time._getStandardFormat(hour, minute),
                Time._getMinuteFormat(hour, minute))

  def parse(time):
    if type(time) == int:
      time %= 720
      if time < 0:
        time += 720
      hour = int(time // 60)
      minute = time % 60
      return Time(Time._getStandardFormat(hour, minute), time)
    
    if type(time) != str:
      return ValueError(f'could not convert {time} to Time')

    time = time.strip()

    m = Time._TIME_PATTERN_STANDARD.match(time)
    if m:
      return Time._timeByHourAndMinute(m.group('hour'), m.group('minute'))

    m = Time._TIME_PATTERN_NOCOLON.match(time)
    if m:
      return Time._timeByHourAndMinute(m.group('hour'), m.group('minute'))
    
    m = Time._TIME_PATTERN_MINUTE.match(time)
    if m:
      return Time._timeByHourAndMinute(0, m.group('minute'))

    raise ValueError(f'could not convert {time} to Time')

  def __repr__(self):
    return f'Time(standard: "{self.standard}", minute: {self.minute})'

  def __str__(self):
    return self.standard

  def __int__(self):
    return self.minute

  def __add__(self, other):
    return Time.parse(int(self) + int(other))

  def __neg__(self):
    return Time.parse(- int(self))

  def __sub__(self, other):
    return Time.parse(int(self) - int(other))

  def __setattr__(self, name, value):
    """ make Time immutable """
    raise AttributeError('could not set value')

_TIME_EXPRESSION_PATTERN = re.compile(r'(?P<time>[^+-]*)(?P<operation>[+-])(?P<remaining>.*)')
_NEGATIVE_TIME_EXPRESSION_PATTERN = re.compile(r'\s*-(?P<remaining>.*)')

def _processAdminCommandAndGetMessage(message, server_id):
  channel = discord_utils.get_channel('subtitles', server_id)
  discord_utils.post_message_in_channel(channel['id'], message)
  return 'Posted message in subtitles.'

def evaluate(expression, channel_id):
  channel = discord_utils.get_channel_by_id(channel_id)
  server_id = channel['guild_id']
  if channel['name'] == 'admin-channel':
    return _processAdminCommandAndGetMessage(expression, server_id)
  original_expression = expression
  total = Time.parse(0)
  evaluated_expression = []
  prev_add = True
  m = _NEGATIVE_TIME_EXPRESSION_PATTERN.match(expression)
  if m:
    expression = m.group('remaining')
    prev_add = False
    evaluated_expression = ['-']

  m = _TIME_EXPRESSION_PATTERN.match(expression)
  while m:
    t = Time.parse(m.group('time'))
    evaluated_expression.append(str(t))
    if prev_add:
      total += t
    else:
      total -= t

    operation = m.group('operation')
    prev_add = operation == '+'
    evaluated_expression.append(operation)

    expression = m.group('remaining')
    m = _TIME_EXPRESSION_PATTERN.match(expression)

  # ending time
  t = Time.parse(expression)
  if prev_add:
    total += t
  else:
    total -= t
  evaluated_expression.append(str(t))

  formatted_evaluated_expression = ' '.join(evaluated_expression)
  return f'Input: "{original_expression}"\nCalculated: "{formatted_evaluated_expression}"\n**{str(total)}**'
