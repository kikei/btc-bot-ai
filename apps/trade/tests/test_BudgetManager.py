import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from BudgetManager import *
from Models import *
from ActionsDispatcher import *

@pytest.fixture
def models():
  return getModels(getDBInstance())

@pytest.fixture
def modelsDummy():
  class Models(object):
    def __init__(self):
      self.Values = ValuesDummy()
  
  class ValuesDummy(object):
    def __init__(self):
      self.values = {
        Values.AdjusterStep: 1.0,
        Values.AdjusterStop: 10.0,
        Values.AdjusterThresConf: 0.8,
        Values.AdjusterSpeed: None,
        Values.AdjusterLastDirection: None
      }

    def get(self, key):
      return self.values[key]

    def set(self, key, value):
      self.values[key] = value
  
  return Models()

def test_init(modelsDummy):
  models = modelsDummy
  creator = BudgetManager(models)
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 0.0
  assert creator.lastDirection == 0


def test_calc(modelsDummy):
  models = modelsDummy
  creator = BudgetManager(models)
  creator.speed = 0.5
  creator.lastDirection = +1
  creator.save()
  assert models.Values.get(Values.AdjusterSpeed) == 0.5
  assert models.Values.get(Values.AdjusterLastDirection) == +1


def test_calc_long(modelsDummy):
  models = modelsDummy
  creator = BudgetManager(models)
  lot = creator.calc(+1)
  assert lot < 1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 1.0
  assert creator.lastDirection == +1

def test_calc_short(modelsDummy):
  models = modelsDummy
  creator = BudgetManager(models)
  lot = creator.calc(-1)
  assert lot > -1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == -1.0
  assert creator.lastDirection == -1

def test_makeDecision_long(modelsDummy):
  class confidence:
    longConf = 0.9
    shortConf = 0.1
  models = modelsDummy
  creator = BudgetManager(models)
  lot = creator.makeDecision(confidence)
  assert lot < 1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == 1.0
  assert creator.lastDirection == +1
  

def test_makeDecision_short(modelsDummy):
  class confidence:
    longConf = 0.1
    shortConf = 0.9
  models = modelsDummy
  creator = BudgetManager(models)
  lot = creator.makeDecision(confidence)
  assert lot > -1.0
  assert creator.step == 1.0
  assert creator.stop == 10.0
  assert creator.thresConf == 0.8
  assert creator.speed == -1.0
  assert creator.lastDirection == -1
  

def test_createAction_long(modelsDummy):
  class confidence:
    longConf = 0.9
    shortConf = 0.1
  models = modelsDummy
  creator = BudgetManager(models)
  action = creator.createAction(confidence)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.OpenLong
  

def test_createAction_short(modelsDummy):
  class confidence:
    longConf = 0.1
    shortConf = 0.9
  models = modelsDummy
  creator = BudgetManager(models)
  action = creator.createAction(confidence)
  assert isinstance(action, Action)
  assert action.name == PlayerActions.OpenShort

