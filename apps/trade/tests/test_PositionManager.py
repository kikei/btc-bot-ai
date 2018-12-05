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

@pytest.fixture
def modelsDummy():
  models = ModelsDummy()
  models.Values.set(Values.PositionThresProfit, 1.1)
  models.Values.set(Values.PositionThresLossCut, 0.9)
  return models

def test_init(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  assert manager.profitThres == 1.1
  assert manager.lossCutThres == 0.9

def test_calcVariation():
  now = datetime.datetime.now()
  exchanger = 'test'
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

def test_createAction_longProfit(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  now = datetime.datetime.now()
  exchanger = 'test'
  tick = OneTick(ask=500000,
                 bid=500000 * models.Values.get(Values.PositionThresProfit))
  models.Ticks.save(Tick({exchanger: tick}))
  
  def longOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  
  positions = [
    Position(now, Position.StatusClose, [longOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [longOne(tick.bid)]), # Not match
    Position(now, Position.StatusOpen, [longOne(500000)])    # Set Profit
  ]
  action = manager.createAction(positions)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForProfit
  assert isinstance(action.args[0], Position)
  assert action.args[0] == positions[2]

def test_createAction_longLossCut(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  now = datetime.datetime.now()
  exchanger = 'test'
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
  action = manager.createAction(positions)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForLossCut
  assert isinstance(action.args[0], Position)
  assert action.args[0] == positions[2]

def test_createAction_shortProfit(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  now = datetime.datetime.now()
  exchanger = 'test'
  tick = OneTick(ask=500000 / models.Values.get(Values.PositionThresProfit),
                 bid=500000)
  models.Ticks.save(Tick({exchanger: tick}))
  
  def shortOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideShort)
  
  positions = [
    Position(now, Position.StatusClose, [shortOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [shortOne(tick.ask)]), # Not match
    Position(now, Position.StatusOpen, [shortOne(500000)])    # Set Profit
  ]
  action = manager.createAction(positions)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForProfit
  assert isinstance(action.args[0], Position)
  assert action.args[0] == positions[2]

def test_createAction_longLossCut(modelsDummy):
  models = modelsDummy
  manager = PositionsManager(models)
  now = datetime.datetime.now()
  exchanger = 'test'
  tick = OneTick(ask=1. + 500000 / models.Values.get(Values.PositionThresLossCut),
                 bid=500000)
  models.Ticks.save(Tick({exchanger: tick}))
  
  def shortOne(price):
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideShort)
  
  positions = [
    Position(now, Position.StatusClose, [shortOne(500000)]),  # Closed
    Position(now, Position.StatusOpen, [shortOne(tick.ask)]), # Not match
    Position(now, Position.StatusOpen, [shortOne(500000)])    # LossCut
  ]
  action = manager.createAction(positions)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForLossCut
  assert isinstance(action.args[0], Position)
  assert action.args[0] == positions[2]
