import os
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from classes import *

def ModelsDummy():
  class Models(object):
    def __init__(self):
      self.Confidences = ConfidencesDummy()
      self.Positions = PositionsDummy()
      self.Ticks = TicksDummy()
      self.Trades = TradesDummy()
      self.Values = ValuesDummy()
  
  class ConfidencesDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, confidence, accountId):
      self.collection[confidence.date] = confidence.toDict()
      return confidence

  class TicksDummy(object):
    def __init__(self):
      self.collection = {}

    def one(self):
      k = sorted(self.collection.keys())[0]
      obj = {}
      for e, t in self.collection[k].items():
        obj[e] = OneTick.fromDict(t)
      return Tick(obj)

    def save(self, tick):
      k = list(tick.ticks.items())[0][1].date.timestamp()
      tick = tick.toDict()
      d = {}
      for e, t in tick.items():
        date = datetime.datetime.fromtimestamp(t['datetime'])
        t['datetime'] = datetimeToStr(date)
        d[e] = t
      self.collection[k] = d
  
  class TradesDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, trade, accountId):
      self.collection[trade.date] = trade.toDict()
      return trade
  
  class PositionsDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, position):
      self.collection[position.date] = position.toDict()
      return position
  
  class ValuesDummy(object):
    def __init__(self):
      self.values = {}
    
    def get(self, key, accountId):
      if key in self.values:
        return self.values[key]
      else:
        return None
    
    def set(self, key, value, accountId):
      self.values[key] = value
  
  return Models()

