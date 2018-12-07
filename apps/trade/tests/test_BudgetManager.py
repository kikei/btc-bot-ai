import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from BudgetManager import *
from ModelsDummy import *
from ActionsDispatcher import *

@pytest.fixture
def accountId():
  return 'test'

@pytest.fixture
def models():
  return getModels(getDBInstance())

@pytest.fixture
def modelsDummy(accountId):
  models = ModelsDummy()
  models.Values.set(Values.AdjusterStep, 1.0, accountId=accountId)
  models.Values.set(Values.AdjusterStop, 10.0, accountId=accountId)
  models.Values.set(Values.AdjusterThresConf, 0.8, accountId=accountId)
  models.Values.set(Values.AdjusterSpeed, None, accountId=accountId)
  models.Values.set(Values.AdjusterLastDirection, None, accountId=accountId)
  return models


def test_init(modelsDummy, accountId):
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 0.0
  assert creator.lastDirection == 0


def test_calc(modelsDummy, accountId):
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  creator.speed = 0.5
  creator.lastDirection = +1
  creator.save()
  assert models.Values.get(Values.AdjusterSpeed, accountId=accountId) == 0.5
  assert models.Values.get(Values.AdjusterLastDirection, accountId=accountId) == +1


def test_calc_long(modelsDummy, accountId):
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  lot = creator.calc(+1)
  assert lot < 1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 1.0
  assert creator.lastDirection == +1

def test_calc_short(modelsDummy, accountId):
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  lot = creator.calc(-1)
  assert lot > -1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == -1.0
  assert creator.lastDirection == -1

def test_makeDecision_long(modelsDummy, accountId=accountId):
  class confidence:
    longConf = 0.9
    shortConf = 0.1
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  lot = creator.makeDecision(confidence)
  assert lot < 1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 1.0
  assert creator.lastDirection == +1
  

def test_makeDecision_short(modelsDummy, accountId):
  class confidence:
    longConf = 0.1
    shortConf = 0.9
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  lot = creator.makeDecision(confidence)
  assert lot > -1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == -1.0
  assert creator.lastDirection == -1
  

def test_createAction_long(modelsDummy, accountId):
  class confidence:
    longConf = 0.9
    shortConf = 0.1
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  action = creator.createAction(confidence)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.OpenLong
  

def test_createAction_short(modelsDummy, accountId):
  class confidence:
    longConf = 0.1
    shortConf = 0.9
  models = modelsDummy
  creator = BudgetManager(models, accountId=accountId)
  action = creator.createAction(confidence)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.OpenShort

