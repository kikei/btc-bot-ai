import datetime
import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from MainOperator import *
from ModelsDummy import *
from ActionsDispatcher import *

# Date utilities
def date(base=None, **a):
  if base is None:
    base = datetime.datetime.now()
  return base + datetime.timedelta(**a)

def saveTrendStrengths(models, strengths, accountId):
  for e in strengths:
    models.TrendStrengths.save(e, accountId=accountId)

def savePositions(models, positions, accountId):
  for e in positions:
    models.Positions.save(e, accountId=accountId)

@pytest.fixture
def accountId():
  return 'test'

@pytest.fixture
def models():
  return getModels(getDBInstance())

@pytest.fixture
def modelsDummy(accountId):
  models = ModelsDummy()
  # Values
  models.Values.set(Values.OperatorLastFired, None, accountId=accountId)
  models.Values.set(Values.OperatorSleepDuration, 1200.0, accountId=accountId)
  models.Values.set(Values.OperatorTrendStrengthLoad, 3600, accountId=accountId)
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  models.Values.set(Values.OperatorTrendGradient, 0.02, accountId=accountId)
  models.Values.set(Values.OperatorTrendSize, 4, accountId=accountId)
  models.Values.set(Values.OperatorLotInit, 0.01, accountId=accountId)
  # TrendStrengths
  trends = [
    TrendStrength(date(minutes=-70), 0.80),
    TrendStrength(date(minutes=-60), 0.70),
    TrendStrength(date(minutes=-50), 0.65),
    TrendStrength(date(minutes=-40), 0.60),
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(minutes=-20), 0.50),
    TrendStrength(date(minutes=-10), 0.45),
    TrendStrength(date(), 0.40)
  ]
  saveTrendStrengths(models, trends, accountId)
  return models


def test_init(modelsDummy, accountId):
  models = modelsDummy
  creator = MainOperator(models, accountId=accountId)

def test_getStoredValue(modelsDummy, accountId):
  models = modelsDummy
  creator = MainOperator(models, accountId=accountId)
  keys = [
    Values.OperatorSleepDuration,
    Values.OperatorLotInit,
    Values.OperatorTrendGradient,
    Values.OperatorTrendSize,
    Values.OperatorTrendWidth,
    Values.OperatorTrendStrengthLoad
  ]
  for k in keys:
    expect = models.Values.get(k, accountId=accountId)
    actual = creator.getStoredValue(k)
    assert expect == actual

def test_getCurrentEntries(modelsDummy, accountId):
  models = modelsDummy
  creator = MainOperator(models, accountId=accountId)
  entries = creator.getCurrentEntries()
  assert len(entries) == 6
  for e in entries:
    assert isinstance(e, TrendStrength)

def test_getOpenPositions(modelsDummy, accountId):
  models = modelsDummy
  creator = MainOperator(models, accountId=accountId)
  longs, shorts = creator.getOpenPositions()
  assert len(longs) == 0
  assert len(shorts) == 0

def test_isSleeping(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorSleepDuration, 1200.0, accountId=accountId)
  creator = MainOperator(models, accountId=accountId)
  models.Values.set(Values.OperatorLastFired, None, accountId=accountId)
  assert not creator.isSleeping()
  models.Values.set(Values.OperatorLastFired, date(minutes=-10).timestamp(),
                    accountId=accountId)
  assert creator.isSleeping()
  models.Values.set(Values.OperatorLastFired, date(minutes=-21).timestamp(),
                    accountId=accountId)
  assert not creator.isSleeping()

def test_checkEntriesSize(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendSize, 4, accountId=accountId)
  creator = MainOperator(models, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-20), 0.55),
    TrendStrength(date(minutes=-10), 0.50),
    TrendStrength(date(), 0.45)
  ]
  assert not creator.checkEntriesSize(entries)
  entries = [
    TrendStrength(date(minutes=-40), 0.55),
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(minutes=-20), 0.55),
    TrendStrength(date(minutes=-10), 0.50),
    TrendStrength(date(), 0.45)
  ]
  assert creator.checkEntriesSize(entries)

def test_checkEntriesTimeWidth(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  creator = MainOperator(models, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-29), 0.55),
    TrendStrength(date(), 0.45)
  ]
  assert not creator.checkEntriesTimeWidth(entries)
  entries = [
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(), 0.45)
  ]
  assert creator.checkEntriesTimeWidth(entries)

def test_makeDecision_notEnoughGradient(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  models.Values.set(Values.OperatorTrendGradient, 0.2, accountId=accountId)
  models.Values.set(Values.OperatorTrendSize, 2, accountId=accountId)
  creator = MainOperator(models, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(), 0.45)
  ]
  chance = creator.makeDecision(entries)
  assert chance == 0

def test_makeDecision(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  models.Values.set(Values.OperatorTrendGradient, 0.02, accountId=accountId)
  models.Values.set(Values.OperatorTrendSize, 4, accountId=accountId)
  creator = MainOperator(models, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(minutes=-20), 0.50),
    TrendStrength(date(minutes=-10), 0.45),
    TrendStrength(date(), 0.40)
  ]
  chance = creator.makeDecision(entries)
  assert chance < 0

def test_calculateLot(modelsDummy, accountId):
  models = modelsDummy
  creator = MainOperator(models, accountId=accountId)
  lot = creator.calculateLot(chance=1)
  assert lot == 0.01
  lot = creator.calculateLot(chance=-1)
  assert lot == -0.01

def test_createAction_openShort(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  models.Values.set(Values.OperatorTrendGradient, 0.02, accountId=accountId)
  models.Values.set(Values.OperatorTrendSize, 4, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(minutes=-20), 0.50),
    TrendStrength(date(minutes=-10), 0.45),
    TrendStrength(date(), 0.40)
  ]
  saveTrendStrengths(models, entries, accountId)
  creator = MainOperator(models, accountId=accountId)
  action = creator.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.OpenShort

def test_createAction_closeForProfit_long(modelsDummy, accountId):
  models = modelsDummy
  models.Values.set(Values.OperatorTrendWidth, 1800, accountId=accountId)
  models.Values.set(Values.OperatorTrendGradient, 0.02, accountId=accountId)
  models.Values.set(Values.OperatorTrendSize, 4, accountId=accountId)
  entries = [
    TrendStrength(date(minutes=-30), 0.55),
    TrendStrength(date(minutes=-20), 0.50),
    TrendStrength(date(minutes=-10), 0.45),
    TrendStrength(date(), 0.40)
  ]
  def longOne(price):
    exchanger = Tick.BitFlyer
    return OnePosition(exchanger, [1.0], [price], side=OnePosition.SideLong)
  positions = [
    Position(date(days=-1), Position.StatusOpen, [longOne(500000)]),
    Position(date(days=-2), Position.StatusOpen, [longOne(500000)])
  ]
  savePositions(models, positions, accountId)
  creator = MainOperator(models, accountId=accountId)
  action = creator.createAction()
  assert isinstance(action, Action)
  assert action.name == PlayerActions.CloseForProfit
