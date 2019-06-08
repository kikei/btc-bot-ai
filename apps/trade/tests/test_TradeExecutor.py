import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from ModelsDummy import *
from TradeExecutor import *
from market.BitFlyer import BitFlyerAPIError

@pytest.fixture
def accountId():
  return 'test'

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
  return ModelsDummy()

def test_init(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  assert executor.models is not None
  assert executor.trader is not None
  assert executor.logger is not None
  assert executor.minPrecision is not None

def test_roundLot(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  assert executor.roundLot(1.2354321) == 1.24

def test_openPosition(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  exchanger = 'test'
  lot = 1.0
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return one
  trade, position = executor.openPosition(lot, traderFun)
  assert isinstance(trade, Trade)
  assert str(trade.position) == str(one)
  assert str(Trade.fromDict(models.Trades.collection[trade.date])) == str(trade)
  assert isinstance(position, Position)
  assert isinstance(position.date, datetime.datetime)
  assert position.status == Position.StatusOpen
  assert len(position.positions) == 1
  assert position.closed is None
  assert str(Position.fromDict(models.Positions.collection[position.date])) == str(position)

def test_handleOpen_ok(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  exchanger = 'test'
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return position
  result = executor.handleOpen(lot, traderFun)
  assert result is True

def test_handleOpen_lot0(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  exchanger = 'test'
  lot = 0.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert False
  result = executor.handleOpen(lot, traderFun)
  assert result is False

def test_handleOpen_tradeNG(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  exchanger = 'test'
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    assert lot_ == lot
    return None
  result = executor.handleOpen(lot, traderFun)
  assert result is False

def test_handleOpen_tradeError(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, accountId=accountId)
  exchanger = 'test'
  lot = 1.0
  position = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  def traderFun(lot_):
    raise BitFlyerAPIError('error')
  result = executor.handleOpen(lot, traderFun)
  assert result is False

def test_closePosition(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader(), accountId=accountId)
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
  trade = Trade.fromDict(models.Trades.collection[trades[0].date])
  assert str(trade) == str(trades[0])
  assert isinstance(position, Position)
  assert isinstance(position.date, datetime.datetime)
  assert position.status == Position.StatusClose
  assert len(position.positions) == 1
  assert len(position.closed) == len(position.positions)
  assert all(isinstance(p, OnePosition) for p in position.closed)
  pos = Position.fromDict(models.Positions.collection[position.date])
  assert str(pos) == str(position)

def test_handleClose_ok(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader(), accountId=accountId)
  exchanger = 'test'
  date = datetime.datetime.now()
  one = OnePosition(exchanger, [1.0], [1.0], OnePosition.SideLong)
  position = Position(date, Position.StatusOpen, [one])
  result = executor.handleClose(position)
  assert result
  saved = Position.fromDict(models.Positions.collection.popitem()[1])
  assert isinstance(saved, Position)
  assert isinstance(saved.date, datetime.datetime)
  assert saved.status == Position.StatusClose
  assert len(saved.positions) == 1

def test_handleClose_closed(modelsDummy, accountId):
  models = modelsDummy
  executor = TradeExecutor(models, trader=DummyTrader(), accountId=accountId)
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

