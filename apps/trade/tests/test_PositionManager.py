import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from PositionsManager import *
from ActionsDispatcher import *
from ModelsDummy import ModelsDummy

def savePositions(models, positions, accountId):
  for e in positions:
    models.Positions.save(e, accountId=accountId)

@pytest.fixture
def accountId():
  return 'test'

@pytest.fixture
def modelsDummy(accountId):
  models = ModelsDummy()
  models.Values.set(Values.PositionThresProfit, 1.1, accountId=accountId)
  models.Values.set(Values.PositionThresLossCut, 0.9, accountId=accountId)
  return models

def test_init(modelsDummy, accountId):
  models = modelsDummy
  manager = PositionsManager(models, accountId)
  assert manager.profitThres == 1.1
  assert manager.lossCutThres == 0.9

def test_calcVariation():
  now = datetime.datetime.now()
  exchanger = Tick.BitFlyer
  price = 500000
  ask = 510000
  bid = 500900
  tick = OneTick(ask=ask, bid=bid)
  one = OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  assert 1. * bid / price == PositionsManager.calcVariation(tick, one)
  one = OnePosition(exchanger, [1.0], [price], side=OnePosition.SideShort)
  assert 1. * ask / price == PositionsManager.calcVariation(tick, one)
  one = OnePosition(exchanger, [0.7, 0.3], [price, price],
                    side=OnePosition.SideLong)
  assert 1. * bid / price == PositionsManager.calcVariation(tick, one)
  one = OnePosition(exchanger, [0.7, 0.3], [price, price],
                    side=OnePosition.SideShort)
  assert 1. * ask / price == PositionsManager.calcVariation(tick, one)

def test_createAction_longProfit(modelsDummy, accountId):
  models = modelsDummy
  manager = PositionsManager(models, accountId=accountId)
  now = datetime.datetime.now()
  exchanger = Tick.BitFlyer
  tick = OneTick(ask=500000,
                 bid=500000 * models.Values.get(Values.PositionThresProfit,
                                                accountId=accountId))
  models.Ticks.save(Tick({exchanger: tick}))
  
  def longOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  
  positions = [
    Position(now, Position.StatusClose, [longOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [longOne(tick.bid)]), # Not match
    Position(now, Position.StatusOpen, [longOne(500000)])    # Set Profit
  ]
  savePositions(models, positions, accountId)
  action = manager.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForProfit
  assert isinstance(action.args[0], Position)
  assert str(action.args[0]) == str(positions[2])

def test_createAction_longLossCut(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  now = datetime.datetime.now()
  exchanger = Tick.BitFlyer
  tick = OneTick(ask=500000,
                 bid=500000 * models.Values.get(Values.PositionThresLossCut))
  models.Ticks.save(Tick({exchanger: tick}))
  
  def longOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  
  positions = [
    Position(now, Position.StatusClose, [longOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [longOne(tick.bid)]), # Not match
    Position(now, Position.StatusOpen, [longOne(500000)])    # LossCut
  ]
  savePositions(models, positions, accountId)
  action = manager.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForLossCut
  assert isinstance(action.args[0], Position)
  assert action.args[0] == positions[2]

def test_createAction_shortProfit(modelsDummy, accountId):
  models = modelsDummy
  manager = PositionsManager(models, accountId=accountId)
  now = datetime.datetime.now()
  exchanger = Tick.BitFlyer
  tick = OneTick(ask=500000 / models.Values.get(Values.PositionThresProfit,
                                                accountId=accountId),
                 bid=500000)
  models.Ticks.save(Tick({exchanger: tick}))
  
  def shortOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideShort)
  
  positions = [
    Position(now, Position.StatusClose, [shortOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [shortOne(tick.ask)]), # Not match
    Position(now, Position.StatusOpen, [shortOne(500000)])    # Set Profit
  ]
  savePositions(models, positions, accountId)
  action = manager.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForProfit
  assert isinstance(action.args[0], Position)
  assert str(action.args[0]) == str(positions[2])

def test_createAction_longLossCut(modelsDummy, accountId):
  models = modelsDummy
  manager = PositionsManager(models, accountId=accountId)
  now = datetime.datetime.now()
  exchanger = Tick.BitFlyer
  thres = models.Values.get(Values.PositionThresLossCut, accountId=accountId)
  tick = OneTick(ask=1. + 500000 / thres, bid=500000)
  models.Ticks.save(Tick({exchanger: tick}))
  
  def shortOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideShort)
  
  positions = [
    Position(now, Position.StatusClose, [shortOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [shortOne(tick.ask)]), # Not match
    Position(now, Position.StatusOpen, [shortOne(500000)])    # LossCut
  ]
  savePositions(models, positions, accountId)
  action = manager.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForLossCut
  assert isinstance(action.args[0], Position)
  assert str(action.args[0]) == str(positions[2])
