import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from Models import *
from TradeExecutor import *
from market.BitFlyer import BitFlyerAPIError

@pytest.fixture
def models():
  return getModels(getDBInstance())

@pytest.fixture
def modelsDummy():
  class Models(object):
    def __init__(self):
      self.Confidences = ConfidencesDummy()
      self.Trades = TradesDummy()
  
  class ConfidencesDummy(object):
    def __init__(self):
      self.collection = {}
    
    def save(self, confidence):
      self.collection[confidence.date] = confidence
      return confidence

  class TradesDummy(object):
    def __init__(self):
      self.collection = {}

    def save(self, trade):
      self.collection[trade.date] = trade
      return trade
  
  return Models()

def test_init(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  assert executor.models is not None
  assert executor.trader is not None
  assert executor.logger is not None
  assert executor.minPrecision is not None

def test_roundLot(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  assert executor.roundLot(1.2354321) == 1.24

def test_openPosition(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  exchanger = 'test'
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return position
  trade = executor.openPosition(lot, traderFun)
  assert isinstance(trade, Trade)
  assert str(trade.position) == str(position)
  assert models.Trades.collection[trade.date] == trade

def test_handleOpen_ok(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  exchanger = 'test'
  longConf = 0.9
  shortConf = 0.1
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return position
  confidence = Confidence(datetime.datetime.now(),
                          longConf, shortConf, Confidence.StatusNew)
  models.Confidences.save(confidence)
  result = executor.handleOpen(confidence, lot, traderFun)
  assert result is True
  assert confidence.isStatusOf(Confidence.StatusUsed)
  assert models.Confidences.collection[confidence.date] == confidence

def test_handleOpen_lot0(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  exchanger = 'test'
  longConf = 0.9
  shortConf = 0.1
  lot = 0.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert False
  confidence = Confidence(datetime.datetime.now(),
                          longConf, shortConf, Confidence.StatusNew)
  models.Confidences.save(confidence)
  result = executor.handleOpen(confidence, lot, traderFun)
  assert result is False
  assert confidence.isStatusOf(Confidence.StatusNew)
  assert models.Confidences.collection[confidence.date] == confidence

def test_handleOpen_tradeNG(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  exchanger = 'test'
  longConf = 0.9
  shortConf = 0.1
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return None
  confidence = Confidence(datetime.datetime.now(),
                          longConf, shortConf, Confidence.StatusNew)
  models.Confidences.save(confidence)
  result = executor.handleOpen(confidence, lot, traderFun)
  assert result is False
  assert confidence.isStatusOf(Confidence.StatusNew)
  assert models.Confidences.collection[confidence.date] == confidence

def test_handleOpen_tradeError(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models)
  exchanger = 'test'
  longConf = 0.9
  shortConf = 0.1
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    raise BitFlyerAPIError('error')
  confidence = Confidence(datetime.datetime.now(),
                          longConf, shortConf, Confidence.StatusNew)
  models.Confidences.save(confidence)
  result = executor.handleOpen(confidence, lot, traderFun)
  assert result is False
  assert confidence.isStatusOf(Confidence.StatusNew)
  assert models.Confidences.collection[confidence.date] == confidence
