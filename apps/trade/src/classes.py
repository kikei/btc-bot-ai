import datetime

TICK_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def datetimeToStr(d):
  return d.strftime(TICK_DATE_FORMAT)

def strToDatetime(s):
  return datetime.datetime.strptime(s, TICK_DATE_FORMAT)


class OnePosition(object):
  SideLong = 'LONG'
  SideShort = 'SHORT'
  
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
    "DEPRECATED"
    return self.sizeWhole()

  def sizeWhole(self):
    return sum(self.sizes)

  def priceMean(self):
    return self.amount() / self.sizeWhole()
  
  def sideReverse(self):
    if self.side == OnePosition.SideLong:
      return OnePosition.SideShort
    else:
      return OnePosition.SideLong
  
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
  StatusIgnored = 'ignored'
  StatusOpening = 'opening'
  StatusClosing = 'closing'

  def __init__(self, date, status, positions, closed=None):
    """
    (self: Position, date: datetime, status: str,
     positions: [OnePosition], closed: [OnePosition])
    -> Position
    """
    self.date = date
    self.status = status
    self.positions = positions
    self.closed = closed
  
  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    date = datetime.datetime.fromtimestamp(obj['timestamp'])
    status = obj['status']
    positions = [OnePosition.fromDict(p) for p in obj['positions']]
    if 'closed' not in obj or obj['closed'] is None:
      closed = None
    else:
      closed = [OnePosition.fromDict(p) for p in obj['closed']]
    return Position(date, status, positions, closed)
  
  def toDict(self):
    if self.closed is None:
      closed = None
    else:
      closed = [p.toDict() for p in self.closed]
    obj = {
      'timestamp': self.date.timestamp(),
      'status': self.status,
      'positions': [p.toDict() for p in self.positions],
      'closed': closed
    }
    return obj
  
  def __str__(self):
    positions = ', '.join(str(p) for p in self.positions)
    if self.closed is None:
      closed = None
    else:
      closed = ', '.join(str(p) for p in self.closed)
    text = (('Position(date={date}, status={status}, ' +
             'positions=[{positions}], closed=[{closed}])')
            .format(date=datetimeToStr(self.date), status=self.status,
                    positions=positions, closed=closed))
    return text
  
  def isNotClosed(self):
    return self.status in [Position.StatusOpen, Position.StatusOpening]
  
  def isOpen(self):
    return self.status in [Position.StatusOpen]
  
  def setClosed(self, closed):
    self.closed = closed
  
  def setStatus(self, status):
    self.status = status

class Confidence(object):
  StatusNew = 'new'
  StatusUsed = 'used'
  StatusIgnored = 'ignored'
  
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
      date = datetime.datetime.now()
    self.date = date

  def spread(self):
    return self.ask - self.bid

  @staticmethod
  def fromDict(obj):
    if obj is None:
      return None
    date = strToDatetime(obj['datetime'])
    one = OneTick(obj['ask'], obj['bid'], date)
    return one
  
  def toDict(self):
    obj = {
      'datetime': self.date.timestamp(),
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
    d = {}
    for e in self.exchangers():
      if self.exchanger(e) is not None:
        d[e] = self.exchanger(e).toDict()
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
  OpenLong: (confidence: Confidence, lot: float)
  OpenShort: (confidence: Confidence, lot: float)
  CloseForProfit: (position: Position)
  CloseForLossCut: (position: Position)
  Exit: ()
  """
  OpenLong = 'OpenLong'
  OpenShort = 'OpenShort'
  IgnoreConfidence = 'IgnoreConfidence'
  CloseForProfit = 'CloseForProfit'
  CloseForLossCut = 'CloseForLossCut'
  Exit = 'Exit'
