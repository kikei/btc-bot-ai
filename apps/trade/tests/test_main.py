import datetime
import os
import pytest
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *

@pytest.fixture
def accountId():
  return 'test'

@pytest.fixture
def models():
  return getModels(getDBInstance())

def test_checkProperties():
  assert checkProperties()
