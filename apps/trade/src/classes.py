import datetime

TICK_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def datetimeToStr(d):
  return d.strftime(TICK_DATE_FORMAT)

def strToDatetime(s):
  return datetime.datetime.strptime(s, TICK_DATE_FORMAT)


class OnePosition(object):
  SideLong = 'long'
  SideShort = 'short'
  
  def __init__(self, exchanger, sizes, prices, ids=None, side=None):
    self.exchanger = exchanger
    self.sizes = sizes
    self.prices = prices
    self.ids = ids
    self.side = side
  
  def toDict(self):
    obj = {
      'exchanger': self.exchanger,
      'sizes': self.sizes,
      'prices': self.prices,
      'ids': self.ids,
      'side': self.side
    }
    return obj
  
  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    one = OnePosition(obj['exchanger'],
                      obj['sizes'], obj['prices'], obj['ids'], obj['side'])
    return one
  
  def amount(self):
    return OnePosition.inner_product(self.sizes, self.prices)
  
  def whole_size(self):
    return sum(self.sizes)
  
  def __str__(self):
    text = (('OnePosition(exchanger={exchanger}, ' +
             'sizes={sizes}, prices={prices}, ids={ids}, side={side}')
            .format(exchanger=self.exchanger,
                    sizes=self.sizes, prices=self.prices,
                    ids=self.ids, side=self.side))
    return text
  
  @staticmethod
  def inner_product(A, B):
    return sum(a * b for (a, b) in zip(A, B))


class Position(object):
  StatusOpen = 'open'
  StatusClose = 'close'
  StatusReset = 'reset'
  StatusOpening = 'opening'
  StatusClosing = 'closing'

  def __init__(self, date, status, positions):
    self.date = date
    self.status = status
    self.positions = positions
  
  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    date = datetime.datetime.fromtimestamp(obj['timestamp'])
    status = obj['status']
    positions = [OnePosition.fromDict(p) for p in obj['positions']]
    return Position(date, status, positions)
  
  def toDict(self):
    obj = {
      'timestamp': self.date.timestamp(),
      'status': self.status,
      'positions': [p.toDict() for p in self.positions]
    }
    return obj
  
  def __str__(self):
    positions = ', '.join(list(str, self.positions))
    text = ('Position(date={date}, status={status}, positions=[{positions}]'
            .format(datetimeToStr(self.date), self.status,
                    positions=positions))
    return text


class Confidence(object):
  StatusNew = 'new'
  StatusUsed = 'used'
  
  def __init__(self, date, longConf, shortConf, status):
    self.date = date
    self.longConf = longConf
    self.shortConf = shortConf
    self.status = status
  
  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    date = datetime.datetime.fromtimestamp(obj['timestamp'])
    confidence = Confidence(date, obj['long'], obj['short'], obj['status'])
    return confidence
  
  def toDict(self):
    obj = {
      'timestamp': self.date.timestamp(),
      'long': self.longConf,
      'short': self.shortConf,
      'status': self.status
    }
    return obj
  
  def isStatusOf(self, status):
    return self.status == status

  def updateStatus(self, status):
    self.status = status
    return self

  def __str__(self):
    text = (('date={date}, ' +
             'longConf={long:.3f}, shortConf={short:.3f}, status={status}')
            .format(date=datetimeToStr(self.date),
                    long=self.longConf, short=self.shortConf,
                    status=self.status))
    text = 'Confidence(' + text + ')'
    return text


class Trade(object):
  def __init__(self, date, position):
    self.date = date
    self.position = position

  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    date = datetime.datetime.fromtimestamp(obj['timestamp'])
    position = OnePosition.fromDict(obj['position'])
    trade = Trade(date, position)
    return trade
    
  def toDict(self):
    obj = {
      'timestamp': self.date.timestamp(),
      'position': self.position.toDict()
    }
    return obj
  
  def __str__(self):
    return ('Trade(date={date}, position={position})'
            .format(date=datetimeToStr(self.date), position=str(self.position)))

class OneTick(object):
  def __init__(self, ask, bid, date=None):
    self.ask = float(ask)
    self.bid = float(bid)
    if date is None:
      date = OneTick.date_string()
    self.date = date

  def spread(self):
    return self.ask - self.bid

  @staticmethod
  def date_string(time=None):
    if time is None:
      time = datetime.now()
    date = time.strftime("%Y-%m-%d %H:%M:%S")
    return date

  @staticmethod
  def from_dict(obj):
    if obj is None:
      return None
    one = OneTick(obj['ask'], obj['bid'], obj['datetime'])
    return one
  
  def to_dict(self):
    obj = {
      'datetime': self.date,
      'ask': self.ask,
      'bid': self.bid
    }
    return obj
    
  def __str__(self):
    return ('OneTick(ask={}, bid={}, date={}'
            .format(self.ask, self.bid, self.date))


class Tick(object):
  BitFlyer = 'bitflyer'
  Quoine = 'quoine'
  
  def __init__(self, ticks):
    self.ticks = ticks

  def exchanger(self, name):
    if name in self.ticks:
      return self.ticks[name]
    else:
      return None

  @staticmethod
  def exchangers():
    return [Tick.BitFlyer, Tick.Quoine]

  def toDict(self):
    d = {e: self.exchanger(e).toDict() for e in self.exchangers()}
    return d

  def __str__(self):
    if self.ticks is None:
      text = 'None'
    else:
      text = ', '.join('{}: {:7.1f}/{:7.1f}'.format(e, ot.ask, ot.bid)
                       for e, ot in self.ticks.items()
                       if ot is not None)
    text = 'Tick(' + text + ')'
    return text


class Balance(object):
  def __init__(self, jpy, btc):
    self.jpy_amount = jpy
    self.btc_amount = btc

  def jpy(self, v=None):
    if v is not None:
      self.jpy_amount = v
    return self.jpy_amount

  def btc(self, v=None):
    if v is not None:
      self.btc_amount = v
    return self.btc_amount

  def __str__(self):
    return "jpy: {}, btc: {}".format(self.jpy_amount, self.btc_amount)


class PlayerActions:
  """
  Open: (confidence: Confidence, lot: float)
  Exit: ()
  """
  OpenLong = 'OpenLong'
  OpenShort = 'OpenShort'
  Exit = 'Exit'
