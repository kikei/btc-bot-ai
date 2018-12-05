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

class DummyTrader(object):
  def closePosition(self, position):
    size = position.sizeWhole()
    price = position.priceMean()
    return OnePosition(position.exchanger, [size/2.0, size/2.0],
                       [price*2.0, price*2.0], side=position.sideReverse())

@pytest.fixture
def modelsDummy():
  class Models(object):
    def __init__(self):
      self.Confidences = ConfidencesDummy()
      self.Trades = TradesDummy()
      self.Positions = PositionsDummy()
  
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
  
  class PositionsDummy(object):
    def __init__(self):
      self.collection = {}

    def save(self, position):
      self.collection[position.date] = position
      return position
  
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
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return one
  trade, position = executor.openPosition(lot, traderFun)
  assert isinstance(trade, Trade)
  assert str(trade.position) == str(one)
  assert models.Trades.collection[trade.date] == trade
  assert isinstance(position, Position)
  assert isinstance(position.date, datetime.datetime)
  assert position.status == Position.StatusOpen
  assert len(position.positions) == 1
  assert models.Positions.collection[position.date] == position

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

def test_closePosition(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader())
  exchanger = 'test'
  lot = 1.0
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_): return one
  _, position = executor.openPosition(lot, traderFun)
  trades, position = executor.closePosition(position)
  assert(len(trades) == 1)
  assert isinstance(trades[0], Trade)
  assert isinstance(trades[0].date, datetime.datetime)
  assert trades[0].position.sizeWhole() == one.sizeWhole()
  assert models.Trades.collection[trades[0].date] == trades[0]
  assert isinstance(position, Position)
  assert isinstance(position.date, datetime.datetime)
  assert position.status == Position.StatusClose
  assert len(position.positions) == 1
  assert models.Positions.collection[position.date] == position

def test_handleClose_ok(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader())
  exchanger = 'test'
  date = datetime.datetime.now()
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  position = Position(date, Position.StatusOpen, [one])
  result = executor.handleClose(position)
  assert result
  saved = models.Positions.collection.popitem()[1]
  assert isinstance(saved, Position)
  assert isinstance(saved.date, datetime.datetime)
  assert saved.status == Position.StatusClose
  assert len(saved.positions) == 1

def test_handleClose_closed(modelsDummy):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader())
  exchanger = 'test'
  date = datetime.datetime.now()
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  position = Position(date, Position.StatusClose, [one])
  result = executor.handleClose(position)
  assert not result
  assert len(models.Positions.collection) == 0

def test_handleClose_tradeError(modelsDummy):
  class ErrorTrader(object):
    def closePosition(self, position):
      raise BitFlyerAPIError('error')
  models = modelsDummy
  executor = TradeExecutor(models, ErrorTrader())
  exchanger = 'test'
  date = datetime.datetime.now()
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  position = Position(date, Position.StatusOpen, [one])
  result = executor.handleClose(position)
  assert result is False

