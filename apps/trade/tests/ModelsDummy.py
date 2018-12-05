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
    
    def save(self, confidence):
      self.collection[confidence.date] = confidence
      return confidence

  class TicksDummy(object):
    def __init__(self):
      self.collection = {}

    def one(self):
      k = sorted(self.collection.keys())[0]
      return self.collection[k]

    def save(self, tick):
      k = list(tick.ticks.items())[0][1].date.timestamp()
      self.collection[k] = tick
  
  class TradesDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, trade):
      self.collection[trade.date] = trade
      return trade
  
  class PositionsDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, position):
      self.collection[position.date] = position
      return position
  
  class ValuesDummy(object):
    def __init__(self):
      self.values = {}
    
    def get(self, key):
      return self.values[key]
    
    def set(self, key, value):
      self.values[key] = value
  
  return Models()

