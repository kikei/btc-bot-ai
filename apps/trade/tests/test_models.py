import datetime
import os
import sys

CWD = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(CWD, '..', 'src'))

from main import *
from classes import *
from Models import *

def test_Positions_filterOpen_open():
  now = datetime.datetime.now()
  positions1 = [
      Position(now, Position.StatusOpening, []),
      Position(now - datetime.timedelta(days=-1), Position.StatusOpen, []),
      Position(now - datetime.timedelta(days=-2), Position.StatusOpen, []),
      Position(now - datetime.timedelta(days=-3), Position.StatusClose, [])
  ]
  positions2 = Positions.filterOpen(positions1)
  assert len(positions2) == 2
  assert len(positions2) == len(list(filter(lambda p:p.isOpen(), positions2)))
  assert positions2[0].date == now - datetime.timedelta(days=-1)
  assert positions2[1].date == now - datetime.timedelta(days=-2)

def test_Positions_filterOpen_opening():
  now = datetime.datetime.now()
  positions1 = [
      Position(now, Position.StatusOpening, []),
      Position(now - datetime.timedelta(days=-1), Position.StatusOpening, []),
  ]
  positions2 = Positions.filterOpen(positions1)
  assert len(positions2) == 0

def test_Positions_filterOpen_close():
  now = datetime.datetime.now()
  positions1 = [
      Position(now, Position.StatusClose, []),
      Position(now - datetime.timedelta(days=-1), Position.StatusOpen, []),
  ]
  positions2 = Positions.filterOpen(positions1)
  assert len(positions2) == 0

def test_Positions_filterOpen_closing():
  now = datetime.datetime.now()
  positions1 = [
      Position(now, Position.StatusClosing, []),
      Position(now - datetime.timedelta(days=-1), Position.StatusOpen, []),
  ]
  positions2 = Positions.filterOpen(positions1)
  assert len(positions2) == 0

