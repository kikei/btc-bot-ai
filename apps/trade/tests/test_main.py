import datetime
import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *

class OKPlayer(object):
  def __init__(self, models, logger=None): pass
  def run(self): assert True

class NGPlayer(object):
  def __init__(self, models, logger=None): pass
  def run(self): assert False

@pytest.fixture
def models():
  return getModels(getDBInstance())

def test_checkProperties():
  assert checkProperties()

def test_ConfidenceListener_ok():
  confidence = Confidence(datetime.datetime.now(), 0, 0, Confidence.StatusNew)
  listener = ConfidenceListener(models, Player=OKPlayer)
  listener.handleEntry(confidence)

def test_ConfidenceListener_None():
  listener = ConfidenceListener(models, Player=NGPlayer)
  listener.handleEntry(None)

def test_ConfidenceListener_expired():
  confidence = Confidence(datetime.datetime.now() - datetime.timedelta(hours=1),
                          0, 0, Confidence.StatusNew)
  listener = ConfidenceListener(models, Player=NGPlayer)
  listener.handleEntry(confidence)

def test_ConfidenceListener_used():
  confidence = Confidence(datetime.datetime.now(), 0, 0, Confidence.StatusUsed)
  listener = ConfidenceListener(models, Player=NGPlayer)
  listener.handleEntry(confidence)

def test_PositionListener_list():
  exchanger = 'test'
  positions = [Position(datetime.datetime.now(), Position.StatusOpening, [])]
  listener = PositionListener(models, Player=OKPlayer)
  listener.handleEntry(positions)

def test_PositionListener_empty():
  listener = PositionListener(models, Player=NGPlayer)
  listener.handleEntry([])
