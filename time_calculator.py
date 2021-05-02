import re

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

  def negate(self):
    return Time.parse((720 - self.minute) % 720)

  def __repr__(self):
    return f'Time(standard: {self.standard}, minute: {self.minute})'

  def __str__(self):
    return repr(self)

  def __setattr__(self, name, value):
    """ make Time immutable """
    raise AttributeError('could not set value')

def _add(times):
  return Time.parse(sum(t.minute for t in times) % 720)

def evaluate(expression):
  split_by_plus = expression.split('+')
  # each element starts with a positive time followed by any number of negative times
  # e.g. 1:00 - 0:30 - 0:15
  split_by_minus = [expr.split('-') for expr in split_by_plus]
  times_to_add = []
  msg = []
  for times in split_by_minus:
    # first time is positive, all others are negative
    head = Time.parse(times[0])
    times_to_add.append(head)
    msg.append(f' + {head.standard}')
    tail = [Time.parse(t) for t in times[1:]]
    times_to_add += [t.negate() for t in tail]
    msg += [f' - {t.standard}' for t in tail]
  if msg[0].startswith(' + '):
    msg[0] = msg[0][3:]
  print(''.join(msg))
  return _add(times_to_add).standard
